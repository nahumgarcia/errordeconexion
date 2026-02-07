#!/usr/bin/env python3
"""
Extrae el contenido completo de los posts del dump SQL de WordPress
y actualiza los archivos en _posts/.
Uso: python3 scripts/update_from_sql.py
"""

import os
import re
import glob

SQL_PATH = os.path.join(os.path.dirname(__file__), '..', 'db775240393_hosting-data_io.sql')
POSTS_DIR = os.path.join(os.path.dirname(__file__), '..', '_posts')

# Columnas del INSERT INTO edc_posts:
# 0:ID, 1:post_author, 2:post_date, 3:post_date_gmt, 4:post_content,
# 5:post_title, 6:post_excerpt, 7:post_status, 8:comment_status,
# 9:ping_status, 10:post_password, 11:post_name, 12:to_ping, 13:pinged,
# 14:post_modified, 15:post_modified_gmt, 16:post_content_filtered,
# 17:post_parent, 18:guid, 19:menu_order, 20:post_type,
# 21:post_mime_type, 22:comment_count


def parse_row(text, start):
    """Parsea una fila SQL (ID, ..., count) desde la posicion start.
    Devuelve (fields, next_pos) o (None, next_pos) si falla."""
    i = start

    # Buscar '('
    while i < len(text) and text[i] != '(':
        i += 1
    if i >= len(text):
        return None, i

    i += 1  # saltar '('
    fields = []
    depth = 0

    while i < len(text):
        # Saltar espacios
        while i < len(text) and text[i] in (' ', '\n', '\r'):
            i += 1

        if i >= len(text):
            break

        if text[i] == ')' and depth == 0:
            i += 1
            return fields, i

        if text[i] == "'":
            # String entre comillas simples
            i += 1
            val = []
            while i < len(text):
                if text[i] == '\\' and i + 1 < len(text):
                    val.append(text[i:i+2])  # mantener escape para procesar despues
                    i += 2
                elif text[i] == "'":
                    if i + 1 < len(text) and text[i + 1] == "'":
                        val.append("'")
                        i += 2
                    else:
                        i += 1
                        break
                else:
                    val.append(text[i])
                    i += 1
            fields.append(''.join(val))
        elif text[i:i+4] == 'NULL':
            fields.append(None)
            i += 4
        else:
            # Numero u otro valor
            val = []
            while i < len(text) and text[i] not in (',', ')', '\n'):
                val.append(text[i])
                i += 1
            fields.append(''.join(val).strip())

        # Saltar coma
        while i < len(text) and text[i] in (' ', '\n', '\r'):
            i += 1
        if i < len(text) and text[i] == ',':
            i += 1
        elif i < len(text) and text[i] == ')':
            i += 1
            return fields, i

    return fields if fields else None, i


def unescape_sql(text):
    """Desescapa strings SQL de MySQL."""
    if not text:
        return ''
    text = text.replace('\\n', '\n')
    text = text.replace('\\r', '')
    text = text.replace('\\t', '\t')
    text = text.replace("\\'", "'")
    text = text.replace('\\"', '"')
    text = text.replace('\\\\', '\\')
    return text


def normalize_title(title):
    """Normaliza un titulo para comparacion."""
    t = title.lower().strip()
    t = re.sub(r'^#?\s*', '', t)
    t = re.sub(r'^ep\d+:\s*', '', t)
    t = re.sub(r'^\d+:\s*', '', t)
    return t


def main():
    print('Leyendo SQL dump...')
    with open(SQL_PATH, 'r', encoding='utf-8') as f:
        sql = f.read()

    # Encontrar todas las secciones de INSERT INTO edc_posts
    posts = {}  # guid -> data
    in_edc_posts = False
    pos = 0

    # Buscar cada INSERT INTO edc_posts y parsear sus filas
    insert_marker = "INSERT INTO `edc_posts`"
    values_marker = "VALUES\n"

    idx = 0
    while True:
        idx = sql.find(insert_marker, idx)
        if idx == -1:
            break

        # Buscar VALUES
        val_idx = sql.find(values_marker, idx)
        if val_idx == -1:
            val_idx = sql.find("VALUES ", idx)
        if val_idx == -1:
            idx += len(insert_marker)
            continue

        pos = val_idx + len(values_marker)

        # Parsear filas hasta encontrar un ';' fuera de quotes
        while pos < len(sql):
            fields, pos = parse_row(sql, pos)
            if fields is None:
                break

            if len(fields) >= 23:
                post_status = unescape_sql(fields[7]) if fields[7] else ''
                post_type = unescape_sql(fields[20]) if fields[20] else ''

                if post_status == 'publish' and post_type == 'post':
                    post_content = unescape_sql(fields[4]) if fields[4] else ''
                    post_title = unescape_sql(fields[5]) if fields[5] else ''
                    post_name = unescape_sql(fields[11]) if fields[11] else ''
                    guid = unescape_sql(fields[18]) if fields[18] else ''

                    posts[guid] = {
                        'id': fields[0],
                        'title': post_title,
                        'content': post_content,
                        'post_name': post_name,
                    }

            # Saltar separador entre filas
            while pos < len(sql) and sql[pos] in (' ', '\n', '\r'):
                pos += 1
            if pos < len(sql) and sql[pos] == ',':
                pos += 1
            elif pos < len(sql) and sql[pos] == ';':
                pos += 1
                break
            else:
                break

        idx = pos

    print(f'Encontrados {len(posts)} posts publicados en la BD')
    for guid, data in posts.items():
        print(f"  [{data['id']}] {data['title']}")

    # Indexar por titulo normalizado y post_name
    posts_by_key = {}
    for guid, data in posts.items():
        norm = normalize_title(data['title'])
        posts_by_key[norm] = data
        if data['post_name']:
            posts_by_key[data['post_name']] = data

    # Actualizar archivos _posts
    md_files = sorted(glob.glob(os.path.join(POSTS_DIR, '*.md')))
    updated = 0
    not_found = []

    for md_path in md_files:
        with open(md_path, 'r', encoding='utf-8') as f:
            content = f.read()

        fm_match = re.match(r'^---\n(.+?)\n---\n?(.*)', content, re.DOTALL)
        if not fm_match:
            continue

        front_matter = fm_match.group(1)

        guid_m = re.search(r'^guid:\s*"(.+?)"', front_matter, re.MULTILINE)
        title_m = re.search(r'^title:\s*"(.+?)"', front_matter, re.MULTILINE)

        guid = guid_m.group(1) if guid_m else ''
        title = title_m.group(1) if title_m else ''

        # Buscar por guid
        db_post = posts.get(guid)

        # Buscar por titulo normalizado
        if not db_post and title:
            norm = normalize_title(title)
            db_post = posts_by_key.get(norm)

        # Buscar por post_name extraido del permalink
        if not db_post:
            perm_m = re.search(r'^permalink:\s*/(.+?)/', front_matter, re.MULTILINE)
            if perm_m:
                db_post = posts_by_key.get(perm_m.group(1))

        if not db_post:
            not_found.append(os.path.basename(md_path))
            continue

        new_content = db_post['content'].strip()

        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(f'---\n{front_matter}\n---\n{new_content}\n')

        updated += 1
        print(f'  Actualizado: {os.path.basename(md_path)}')

    print(f'\nResultado: {updated} posts actualizados')
    if not_found:
        print(f'No encontrados en BD: {not_found}')


if __name__ == '__main__':
    main()
