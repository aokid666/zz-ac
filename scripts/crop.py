#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""从已渲染的页 JPEG 裁切解析册图片 —— 输出原格式 JPEG，不做格式转码。

环境变量：
  DPI      渲染 DPI（须与渲染步骤一致，默认 270）
  JPEG_Q   输出 JPEG 质量（默认 95，接近无损）
  PCACHE   页 JPEG 目录（默认 /tmp/pg）
  OUTDIR   输出目录（默认 <repo>/img/ac）
"""
import json, os, re, glob
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DPI = float(os.environ.get('DPI', '270'))
Q = int(os.environ.get('JPEG_Q', '95'))
PCACHE = os.environ.get('PCACHE', '/tmp/pg')
OUTDIR = os.environ.get('OUTDIR', os.path.join(ROOT, 'img', 'ac'))


def page_index():
    idx = {}
    for f in glob.glob(os.path.join(PCACHE, '*.jpg')):
        m = re.search(r'-(\d+)\.jpg$', f)
        if m:
            idx[int(m.group(1))] = f
    return idx


def main():
    crops = json.load(open(os.path.join(ROOT, 'crops.json'), encoding='utf-8'))
    pages = page_index()
    print('页缓存 %d 页，题目 %d 个' % (len(pages), len(crops)), flush=True)
    os.makedirs(OUTDIR, exist_ok=True)
    sc = DPI / 72.0
    done = skip = fail = 0
    cache, cache_page = None, -1
    for qid in sorted(crops):
        for i, r in enumerate(crops[qid]):
            page, x0, y0, x1, y1 = r[0], r[1], r[2], r[3], r[4]
            dst = os.path.join(OUTDIR, '%s_%d.jpg' % (qid, i))
            if os.path.exists(dst) and os.path.getsize(dst) > 1000:
                skip += 1
                continue
            p = pages.get(page)
            if not p:
                fail += 1
                continue
            if page != cache_page:
                if cache is not None:
                    cache.close()
                cache = Image.open(p).convert('RGB')
                cache_page = page
            im = cache
            box = (max(0, round(x0 * sc)), max(0, round(y0 * sc)),
                   min(im.width, round(x1 * sc)), min(im.height, round(y1 * sc)))
            if box[2] - box[0] < 20 or box[3] - box[1] < 20:
                fail += 1
                continue
            im.crop(box).save(dst, 'JPEG', quality=Q, subsampling=0, optimize=True)
            done += 1
            if done % 200 == 0:
                print('  已裁 %d 张' % done, flush=True)
    print('完成：新裁 %d，跳过 %d，失败 %d' % (done, skip, fail), flush=True)


if __name__ == '__main__':
    main()
