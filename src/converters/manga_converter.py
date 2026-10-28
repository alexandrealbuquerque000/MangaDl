import os
import zipfile
import re
import uuid
from datetime import datetime
from PIL import Image, ImageEnhance, ImageFile
from pypdf import PdfWriter
from cbz.comic import ComicInfo
from cbz.constants import PageType, YesNo, Manga, Format
from cbz.page import PageInfo
from src.core.config import WEBTOON_ASPECT_RATIO_THRESHOLD
from src.core.logger import logger

# DOC: Allows loading truncated or partially corrupted images safely
ImageFile.LOAD_TRUNCATED_IMAGES = True

class MangaConverter:
    """
    Handles image preprocessing, cropping, resizing, and building final digital
    formats such as EPUB, PDF, and CBZ.
    """

    @staticmethod
    def natural_keys(text):
        return [(int(c) if c.isdigit() else c) for c in re.split(r'(\d+)', text)]

    @staticmethod
    def _cleanup_temp_images(folders, temp_cover=None):
        for folder in folders:
            if not os.path.exists(folder): 
                continue
            for f in os.listdir(folder):
                if '_opt' in f.lower() or '_part' in f.lower():
                    try: 
                        os.remove(os.path.join(folder, f))
                    except Exception: 
                        pass
        if temp_cover and os.path.exists(temp_cover):
            try: 
                os.remove(temp_cover)
            except Exception: 
                pass

    @staticmethod
    def auto_crop_image(img):
        """Optimized scan to remove white/gray borders, focusing especially on the bottom area."""
        gray = img.convert("L")
        width, height = img.size
        pixels = gray.load()

        bg_thresh = 240

        u = 0
        for y in range(height):
            has_content = False
            for x in range(width):
                if pixels[x, y] < bg_thresh:
                    has_content = True
                    break
            if has_content:
                u = y
                break

        d = height - 1
        for y in range(height - 1, -1, -1):
            has_content = False
            for x in range(width):
                if pixels[x, y] < bg_thresh:
                    has_content = True
                    break
            if has_content:
                d = y
                break

        l = 0
        for x in range(width):
            has_content = False
            for y in range(u, d + 1):
                if pixels[x, y] < bg_thresh:
                    has_content = True
                    break
            if has_content:
                l = x
                break

        r = width - 1
        for x in range(width - 1, -1, -1):
            has_content = False
            for y in range(u, d + 1):
                if pixels[x, y] < bg_thresh:
                    has_content = True
                    break
            if has_content:
                r = x
                break

        padding = 4
        l = max(0, l - padding)
        u = max(0, u - padding)
        r = min(width, r + padding)
        d = min(height, d + padding)

        if (r - l) > (width * 0.4) and (d - u) > (height * 0.4):
            img = img.crop((l, u, r, d))

        return img

    @staticmethod
    def convert_grayscale(img):
        return img.convert('L')

    @staticmethod
    def adjust_contrast(img, factor=1.2):
        enhancer = ImageEnhance.Contrast(img)
        return enhancer.enhance(factor)

    @staticmethod
    def fill_screen_resize(img, target_width, target_height):
        if not target_width or not target_height: 
            return img
        try:
            filter_mode = Image.Resampling.LANCZOS
        except AttributeError:
            filter_mode = getattr(Image, 'LANCZOS', getattr(Image, 'ANTIALIAS', 1))
        return img.resize((target_width, target_height), filter_mode)

    @staticmethod
    def resize_image(img, max_width, max_height):
        if not max_width or not max_height: 
            return img
        if img.width > max_width:
            ratio = max_width / float(img.width)
            new_h = int(img.height * ratio)
            try: 
                filter_mode = Image.Resampling.LANCZOS
            except AttributeError: 
                filter_mode = getattr(Image, 'LANCZOS', getattr(Image, 'ANTIALIAS', 1))
            img = img.resize((max_width, new_h), filter_mode)
        return img

    @staticmethod
    def _process_and_save_image(img, base_path, fmt, options=None, is_cover=False):
        if options is None: 
            options = {}

        KINDLE_MAX_WIDTH = int(options.get('width', 0))
        KINDLE_MAX_HEIGHT = int(options.get('height', 0))
        JPEG_QUALITY = int(options.get('quality', 85))
        WEBTOON_RATIO = WEBTOON_ASPECT_RATIO_THRESHOLD

        if options.get('autocrop', False):
            img = MangaConverter.auto_crop_image(img)

        images_to_process = []
        dp_mode = options.get('double_page_mode', 'Dividir')

        if not is_cover and img.width > img.height * 1.15:
            if dp_mode == "Dividir":
                w_half = img.width // 2
                left_half = img.crop((0, 0, w_half, img.height))
                right_half = img.crop((w_half, 0, img.width, img.height))
                images_to_process = [right_half, left_half] if options.get('rtl', True) else [left_half, right_half]
            elif dp_mode == "Rotacionar":
                img = img.rotate(-90, expand=True)
                images_to_process = [img]
            else:
                images_to_process = [img]
        else:
            images_to_process = [img]

        final_paths = []
        for idx, sub_img in enumerate(images_to_process):
            if options.get('grayscale', False):
                sub_img = MangaConverter.convert_grayscale(sub_img)
            if options.get('contrast', False):
                sub_img = MangaConverter.adjust_contrast(sub_img, factor=options.get('contrast_factor', 1.2))

            if KINDLE_MAX_WIDTH > 0 and KINDLE_MAX_HEIGHT > 0:
                if options.get('fill_screen', False):
                    sub_img = MangaConverter.fill_screen_resize(img, KINDLE_MAX_WIDTH, KINDLE_MAX_HEIGHT)
                else:
                    sub_img = MangaConverter.resize_image(sub_img, KINDLE_MAX_WIDTH, KINDLE_MAX_HEIGHT)

            sub_base = f"{base_path}_{idx}" if len(images_to_process) > 1 else base_path

            if is_cover or KINDLE_MAX_WIDTH == 0 or (sub_img.height / float(sub_img.width) <= WEBTOON_RATIO):
                final_path = f"{sub_base}_opt.jpg"
                sub_img.convert('RGB').save(final_path, format='JPEG', quality=JPEG_QUALITY, optimize=True, progressive=False)
                final_paths.append(final_path)
            else:
                chunk_height = int(sub_img.width * (KINDLE_MAX_HEIGHT / float(KINDLE_MAX_WIDTH)))
                num_parts = (sub_img.height // chunk_height) + (1 if sub_img.height % chunk_height > 0 else 0)

                for p in range(num_parts):
                    top = p * chunk_height
                    bottom = min((p + 1) * chunk_height, sub_img.height)
                    chunk = sub_img.crop((0, top, sub_img.width, bottom))
                    chunk_path = f"{sub_base}_part{p}.jpg"
                    chunk.convert('RGB').save(chunk_path, format='JPEG', quality=JPEG_QUALITY, optimize=True, progressive=False)
                    final_paths.append(chunk_path)

        return final_paths

    @staticmethod
    def prepare_cover(original_path, destination_folder, options=None):
        if not original_path or not os.path.exists(original_path):
            return None
        try:
            dest = os.path.join(destination_folder, f"cover_{uuid.uuid4().hex[:6]}")
            with Image.open(original_path) as opened_img:
                img = opened_img.convert('RGB')
            results = MangaConverter._process_and_save_image(img, dest, fmt='', options=options, is_cover=True)
            return results[0] if results else None
        except Exception as e:
            logger.error(f"Error preparing cover from {original_path}: {e}")
            return None

    @staticmethod
    def check_image(full_path, fmt, options=None, is_cover=False):
        try:
            with Image.open(full_path) as opened_img:
                img = opened_img.convert('RGB')
        except Exception:
            return []

        if img.width < 100 or img.height < 100:
            return []

        base_path, _ = os.path.splitext(full_path)
        return MangaConverter._process_and_save_image(img, base_path, fmt, options=options, is_cover=is_cover)

    @staticmethod
    def create_cbz(folders, destination, cover=None, options=None, cover_source=None):
        try:
            fmt = '.cbz'
            if not destination.endswith(fmt): 
                destination += fmt
            title = os.path.basename(destination).replace(fmt, '')
            pages = []
            if cover and os.path.exists(cover):
                pages.append(PageInfo.load(path=cover, type=PageType.FRONT_COVER))

            abs_cover_source = os.path.abspath(cover_source) if cover_source and os.path.exists(cover_source) else None

            for i, folder in enumerate(folders, 1):
                files = sorted([f for f in os.listdir(folder) if f.lower().endswith(('jpg', 'jpeg', 'png', 'webp')) and not ('_opt' in f.lower() or '_part' in f.lower())], key=MangaConverter.natural_keys)
                for file_name in files:
                    full_img_path = os.path.join(folder, file_name)
                    if abs_cover_source and os.path.abspath(full_img_path) == abs_cover_source:
                        continue
                    paths = MangaConverter.check_image(full_img_path, fmt, options)
                    for p in paths:
                        pages.append(PageInfo.load(path=p, type=PageType.STORY))

            comic = ComicInfo.from_pages(pages=pages, title=title, language_iso='pt', format=Format.WEB_COMIC, black_white=YesNo.NO, manga=Manga.YES)
            with open(destination, "wb") as dest_file:
                dest_file.write(comic.pack())
            logger.info(f"Successfully created CBZ: {destination}")
            return True
        except Exception as e:
            logger.error(f"Error creating CBZ {destination}: {e}")
            return False
        finally:
            MangaConverter._cleanup_temp_images(folders, cover)

    @staticmethod
    def create_pdf(folders, destination, cover=None, options=None, cover_source=None):
        try:
            fmt = '.pdf'
            if not destination.endswith(fmt): 
                destination += fmt
            writer = PdfWriter()
            current_page = 0

            if cover and os.path.exists(cover):
                temp = f"t_c_{uuid.uuid4().hex[:6]}.pdf"
                with Image.open(cover).convert('RGB') as img: 
                    img.save(temp)
                writer.append(temp)
                writer.add_outline_item("Cover", 0)
                current_page += 1
                os.remove(temp)

            abs_cover_source = os.path.abspath(cover_source) if cover_source and os.path.exists(cover_source) else None

            for folder in folders:
                chapter_name = os.path.basename(folder).replace('_', ' ')
                files = sorted([f for f in os.listdir(folder) if f.lower().endswith(('jpg', 'jpeg', 'png', 'webp')) and not ('_opt' in f.lower() or '_part' in f.lower())], key=MangaConverter.natural_keys)
                chapter_start = current_page

                for file_name in files:
                    full_img_path = os.path.join(folder, file_name)
                    if abs_cover_source and os.path.abspath(full_img_path) == abs_cover_source:
                        continue
                    paths = MangaConverter.check_image(full_img_path, fmt, options)
                    for p in paths:
                        temp = f"p_{uuid.uuid4().hex[:6]}.pdf"
                        with Image.open(p).convert('RGB') as img: 
                            img.save(temp)
                        writer.append(temp)
                        current_page += 1
                        os.remove(temp)

                writer.add_outline_item(chapter_name, chapter_start)

            with open(destination, "wb") as f: 
                writer.write(f)
            logger.info(f"Successfully created PDF: {destination}")
            return True
        except Exception as e:
            logger.error(f"Error creating PDF {destination}: {e}")
            return False
        finally:
            MangaConverter._cleanup_temp_images(folders, cover)

    @staticmethod
    def create_epub(folders, destination, cover=None, options=None, cover_source=None):
        if options is None: 
            options = {}
        try:
            fmt = '.epub'
            if not destination.endswith(fmt): 
                destination += fmt
            title = os.path.basename(destination).replace(fmt, '')
            unique_id = str(uuid.uuid4())
            lang = "pt"

            is_rtl = options.get('rtl', True)
            direction = "rtl" if is_rtl else "ltr"
            writing_mode = "horizontal-rl" if is_rtl else "horizontal-lr"

            images_info, spine_refs, toc_items, image_files_to_write = [], [], [], []

            if cover and os.path.exists(cover):
                with Image.open(cover) as img: 
                    w, h = img.size
                page_id = "cover_page"
                img_filename = "cover.jpg"
                images_info.append({"id": "cover_img", "filename": img_filename, "width": w, "height": h, "is_cover": True, "page_id": page_id})
                spine_refs.append(page_id)
                image_files_to_write.append((cover, f"images/{img_filename}"))
                toc_items.append((page_id, "Cover"))

            abs_cover_source = os.path.abspath(cover_source) if cover_source and os.path.exists(cover_source) else None
            global_count = 0

            for i, folder in enumerate(folders, 1):
                chapter_name = os.path.basename(folder).replace('_', ' ')
                files = sorted([f for f in os.listdir(folder) if f.lower().endswith(('jpg', 'jpeg', 'png', 'webp')) and not ('_opt' in f.lower() or '_part' in f.lower())], key=MangaConverter.natural_keys)

                first_page_of_chapter = None
                is_first = True

                for file_name in files:
                    full_img_path = os.path.join(folder, file_name)
                    if abs_cover_source and os.path.abspath(full_img_path) == abs_cover_source:
                        continue

                    is_first_image_of_book = (global_count == 0 and not cover)
                    paths = MangaConverter.check_image(full_img_path, fmt, options, is_cover=is_first_image_of_book)

                    for p in paths:
                        global_count += 1
                        with Image.open(p) as img: 
                            w, h = img.size
                        img_id = f"img_{i}_{global_count}"
                        page_id = f"page_{i}_{global_count}"
                        img_filename = f"image_{global_count:04d}.jpg"

                        images_info.append({"id": img_id, "filename": img_filename, "width": w, "height": h, "is_cover": False, "page_id": page_id})
                        spine_refs.append(page_id)
                        image_files_to_write.append((p, f"images/{img_filename}"))

                        if is_first:
                            first_page_of_chapter = page_id
                            is_first = False

                if first_page_of_chapter:
                    toc_items.append((first_page_of_chapter, chapter_name))

            with zipfile.ZipFile(destination, 'w', zipfile.ZIP_DEFLATED) as zf:
                zf.writestr("mimetype", "application/epub+zip", compress_type=zipfile.ZIP_STORED)
                zf.writestr("META-INF/container.xml", '<?xml version="1.0" encoding="UTF-8"?><container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container"><rootfiles><rootfile full-path="content.opf" media-type="application/oebps-package+xml"/></rootfiles></container>')

                zf.writestr("stylesheet.css", '@charset "utf-8"; body { margin: 0; padding: 0; background-color: #000000; text-align: center; } div { margin: 0; padding: 0; display: block; } img { width: 100%; height: 100%; display: block; margin: 0; padding: 0; }')

                for src, dest in image_files_to_write:
                    try: 
                        zf.write(src, dest)
                    except Exception: 
                        pass

                page_template = '''<?xml version="1.0" encoding="UTF-8"?>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops">
<head>
<title>{title}</title>
<meta name="viewport" content="width={width}, height={height}"/>
<link href="../stylesheet.css" rel="stylesheet" type="text/css"/>
</head>
<body>
<div>
    <img src="../images/{filename}" alt="{title}" />
</div>
</body>
</html>'''

                for info in images_info:
                    zf.writestr(f"pages/{info['page_id']}.xhtml", page_template.format(
                        title=info['page_id'],
                        filename=info['filename'],
                        width=info['width'],
                        height=info['height']
                    ))

                navpoints = "".join([f'<navPoint id="navPoint-{idx}" playOrder="{idx}"><navLabel><text>{title}</text></navLabel><content src="pages/{pid}.xhtml"/></navPoint>' for idx, (pid, title) in enumerate(toc_items, 1)])
                zf.writestr("toc.ncx", f'<?xml version="1.0" encoding="UTF-8"?><ncx xmlns="http://www.daisy.org/z3986/2005/ncx/" version="2005-1"><head><meta name="dtb:uid" content="urn:uuid:{unique_id}"/></head><docTitle><text>{title}</text></docTitle><navMap>{navpoints}</navMap></ncx>')

                toc_li = "".join([f'<li><a href="pages/{pid}.xhtml">{title}</a></li>\n' for pid, title in toc_items])
                zf.writestr("toc.xhtml", f'<?xml version="1.0" encoding="UTF-8"?>\n<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops"><head><title>Table of Contents</title></head><body><nav epub:type="toc" id="toc"><ol>{toc_li}</ol></nav></body></html>')

                manifest_items = '<item id="style" href="stylesheet.css" media-type="text/css"/>\n<item id="ncx" href="toc.ncx" media-type="application/x-dtbncx+xml"/>\n<item id="toc" href="toc.xhtml" media-type="application/xhtml+xml" properties="nav"/>\n'
                for info in images_info:
                    cover_prop = ' properties="cover-image"' if info.get("is_cover") else ''
                    manifest_items += f'<item id="{info["id"]}" href="images/{info["filename"]}" media-type="image/jpeg"{cover_prop}/>\n<item id="{info["page_id"]}" href="pages/{info["page_id"]}.xhtml" media-type="application/xhtml+xml"/>\n'

                spine_items = "".join([f'<itemref idref="{ref}"/>\n' for ref in spine_refs])
                current_datetime = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')

                opf_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="BookID">
<metadata xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:dcterms="http://purl.org/dc/terms/">
    <dc:title>{title}</dc:title>
    <dc:language>{lang}</dc:language>
    <dc:identifier id="BookID">urn:uuid:{unique_id}</dc:identifier>
    <meta property="dcterms:modified">{current_datetime}</meta>
    <meta name="cover" content="cover_img"/>

    <meta name="book-type" content="comic"/>
    <meta name="zero-gutter" content="true"/>
    <meta name="zero-margin" content="true"/>
    <meta name="primary-writing-mode" content="{writing_mode}"/>
    <meta name="RegionMagnification" content="true"/>

    <meta property="rendition:layout">pre-paginated</meta>
    <meta property="rendition:auto">portrait</meta>
    <meta property="rendition:spread">none</meta>
</metadata>
<manifest>
    {manifest_items}
</manifest>
<spine toc="ncx" page-progression-direction="{direction}">
    {spine_items}
</spine>
</package>'''
                zf.writestr("content.opf", opf_content)
            logger.info(f"Successfully created EPUB: {destination}")
            return True
        except Exception as e:
            logger.error(f"Error creating EPUB {destination}: {e}")
            return False
        finally:
            MangaConverter._cleanup_temp_images(folders, cover)
