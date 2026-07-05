"""The browser IS the layout + text-measurement engine. After the archetype
HTML lays out, this script walks every [data-ppt] leaf and returns its
resolved geometry + computed style as a flat primitive list (CSS px)."""

MEASURE_JS = r"""
() => {
  const out = [];
  const norm = s => (s || '').replace(/\s+/g, ' ').trim();
  document.querySelectorAll('[data-ppt]').forEach(el => {
    const r = el.getBoundingClientRect();
    const cs = getComputedStyle(el);
    const kind = el.getAttribute('data-ppt');
    const zAttr = el.getAttribute('data-ppt-z');
    const p = { kind, x: r.left, y: r.top, w: r.width, h: r.height,
                z: zAttr === null ? null : parseInt(zAttr),
                deco: el.getAttribute('data-ppt-deco') !== null };
    if (kind === 'text') {
      const fs = parseFloat(cs.fontSize);
      const lh = cs.lineHeight === 'normal' ? fs * 1.2 : parseFloat(cs.lineHeight);
      const family = (cs.fontFamily.split(',')[0] || '').replace(/["']/g, '').trim();
      Object.assign(p, {
        text: norm(el.textContent),
        fontSizePx: fs,
        fontWeight: parseInt(cs.fontWeight) || 400,
        italic: cs.fontStyle === 'italic',
        family: family,
        color: cs.color,
        align: cs.textAlign,
        lineHeightPx: lh,
        upper: cs.textTransform === 'uppercase',
        letterSpacingPx: cs.letterSpacing === 'normal' ? 0 : parseFloat(cs.letterSpacing),
      });
    } else if (kind === 'rect') {
      const bw = parseFloat(cs.borderTopWidth) || 0;
      const brRaw = cs.borderTopLeftRadius || '0';
      let radiusPx = parseFloat(brRaw) || 0;
      if (brRaw.indexOf('%') >= 0) radiusPx = Math.min(r.width, r.height) * radiusPx / 100;
      Object.assign(p, {
        fill: cs.backgroundColor,
        radiusPx: radiusPx,
        grad: el.getAttribute('data-grad'),
        borderColor: bw > 0 ? cs.borderTopColor : null,
        borderWidthPx: bw,
      });
    } else if (kind === 'image') {
      Object.assign(p, { src: el.getAttribute('data-src') });
    } else if (kind === 'icon') {
      // src is filled in Python after an element screenshot (asset pipeline)
      Object.assign(p, { src: null });
    } else if (kind === 'chart') {
      Object.assign(p, { chart: JSON.parse(el.getAttribute('data-chart')) });
    }
    out.push(p);
  });
  return out;
}
"""
