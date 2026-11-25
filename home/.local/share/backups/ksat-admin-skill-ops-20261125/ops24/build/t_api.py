import pymupdf, sys
print('pymupdf', pymupdf.__version__, pymupdf.mupdf_version if hasattr(pymupdf, 'mupdf_version') else '', pymupdf.__file__)
m = getattr(pymupdf, 'mupdf', None)
print('mupdf 모듈', bool(m))
if m:
    for n in ['fz_outline_glyph', 'fz_render_glyph_pixmap', 'fz_bound_glyph', 'fz_new_text', 'fz_show_glyph', 'fz_fill_text', 'fz_new_draw_device', 'fz_new_pixmap_with_bbox', 'fz_fill_path', 'fz_bound_path', 'fz_walk_path', 'FzPathWalker2', 'fz_new_font_from_buffer', 'fz_advance_glyph', 'fz_glyph_cacheable', 'fz_encode_character', 'fz_new_stext_page_from_page', 'fz_font_ft_face', 'fz_get_glyph_name', 'fz_new_bbox_device', 'fz_new_trace_device']:
        print(f'  {n:28s}', hasattr(m, n))
