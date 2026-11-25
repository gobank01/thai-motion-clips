// Scrapbook engine: builds scenes + GSAP timeline from window.SPEC (spec.js) and window.VO (audio/timing.js).
// All times authored at 1x; master plays at SPEC.speed. Item `at`: [line, "word", offset?] or number (seconds after scene cut).
(() => {
  const S = window.SPEC, VO = window.VO, SPEED = S.speed || 1.1, D = S.duration;
  const vo = (i, w) => { const L = VO[i], k = L.chars.indexOf(w); if (k < 0) throw new Error(`vo(${i}) "${w}" not in ${L.chars}`); return L.t + L.st[k]; };
  const root = document.getElementById("stage"), tl = gsap.timeline({ paused: true });
  const BG = { wood: "assets/desk_wood.jpg", mat: "assets/desk_mat.jpg" };
  const el = (tag, cls, css, html) => { const e = document.createElement(tag); if (cls) e.className = cls; if (css) e.style.cssText = css; if (html != null) e.innerHTML = html; return e; };
  const px = (o) => (o.x != null ? `left:${o.x}px;` : "") + (o.y != null ? `top:${o.y}px;` : "") + (o.size ? `font-size:${o.size}px;` : "") + (o.color ? `color:${o.color};` : "") + (o.d ? `width:${o.d}px;height:${o.d}px;` : "");
  const float = (e, t0, t1, amp = 6) => { const c = 1.6, n = Math.max(1, Math.floor((t1 - t0) / c)); if (t1 - t0 < 1) return;
    tl.to(e, { y: "-=" + amp, rotation: "+=0.7", duration: c / 2, ease: "sine.inOut", yoyo: true, repeat: n * 2 - 1, immediateRender: false }, t0); };
  const DIRS = [{ x: 300 }, { y: 260 }, { x: -300 }, { scale: 1.15 }];
  const cuts = S.scenes.map(sc => Math.max(0, VO[sc.from].t - 0.3)); cuts[0] = 0;
  const cues = [];
  S.scenes.forEach((sc, si) => {
    const t0 = cuts[si], t1 = si + 1 < cuts.length ? cuts[si + 1] : D;
    const sec = el("section", "scene" + (sc.gray ? " gray" : "")); root.appendChild(sec);
    const T = a => a == null ? t0 + 0.2 : typeof a === "number" ? t0 + a : vo(a[0], a[1]) + (a[2] || 0);
    // background
    const b = sc.bg || "wood"; let bgEl;
    if (b === "grid") sec.appendChild(el("div", "grid"));
    else if (b === "paper") sec.appendChild(el("div", "paper"));
    else if (b.startsWith("img:")) { bgEl = el("div", "full", "", `<img src="assets/${b.slice(4)}.png">`); sec.appendChild(bgEl); sec.appendChild(el("div", "shade")); }
    else { bgEl = el("div", "bg", `background-image:url(${BG[b]})`); sec.appendChild(bgEl); }
    tl.set(sec, { opacity: 1 }, t0);
    if (si) { tl.fromTo(sec, { x: 0, y: 0, scale: 1, ...DIRS[si % 4] }, { x: 0, y: 0, scale: 1, duration: 0.45, ease: "power3.out" }, t0); cues.push(["whoosh", t0 - 0.1, 0.25]); }
    if (bgEl) { const z = b.startsWith("img:") ? (si % 2 ? [1.0, 1.16] : [1.18, 1.02]) : [1, 1.08];
      tl.fromTo(bgEl, { scale: z[0], x: 20 }, { scale: z[1], x: -20, duration: t1 - t0 + 0.5, ease: "none" }, t0); }
    if (t1 < D) tl.set(sec, { opacity: 0 }, t1 + 0.45);
    (sc.items || []).forEach(it => {
      const t = T(it.at) - 0.1, rot = it.rot || 0; let e;
      if (it.sticker) {
        e = el("div", "sticker", `left:${it.x}px;top:${it.y}px;width:${it.w || 520}px`, `<img src="assets/st_${it.sticker}.png">`);
        tl.fromTo(e, { opacity: 0, scale: 0.3, y: 260, rotation: rot - 12 }, { opacity: 1, scale: 1, y: 0, rotation: rot, duration: 0.5, ease: "back.out(2)" }, t);
        tl.to(e, { y: -12, rotation: rot + 2, duration: 0.45, ease: "sine.inOut", yoyo: true, repeat: Math.max(1, Math.floor((t1 - t - 0.6) / 0.45)), immediateRender: false }, t + 0.55);
        cues.push(["pop", t, 0.22]);
      } else if (it.logo) {
        const w = it.w || 620, x = it.x != null ? it.x : (1080 - w) / 2;
        e = el("div", "logo", `left:${x}px;top:${it.y || 640}px;width:${w}px` + (it.bg ? `;background:${it.bg}` : ""), `<img src="assets/logo_${it.logo}.${it.ext || "png"}">`);
        tl.fromTo(e, { opacity: 0, scale: 0.2, rotation: rot - 25 }, { opacity: 1, scale: 1, rotation: rot, duration: 0.55, ease: "back.out(2.2)" }, t);
        float(e, t + 0.6, t1, 5); cues.push(["pop", t, 0.25]);
      } else if (it.pol) {
        e = el("div", "pol", `left:${it.x}px;top:${it.y}px;width:${it.w}px;height:${it.h}px`, `<img src="assets/${it.pol}.png"${it.pos ? ` style="object-position:${it.pos}"` : ""}>` + (it.cap ? `<div class="cap">${it.cap}</div>` : ""));
        const from = { top: { y: -800 }, bottom: { y: 800 }, left: { x: -900 }, right: { x: 900 } }[it.from || "top"];
        tl.fromTo(e, { opacity: 0, x: 0, y: 0, rotation: rot - 14, ...from }, { opacity: 1, x: 0, y: 0, rotation: rot, duration: 0.55, ease: "back.out(1.5)" }, t);
        tl.fromTo(e.firstChild, { scale: 1.15 }, { scale: 1, duration: Math.max(1, t1 - t), ease: "none" }, t);
        float(e, t + 0.6, t1, 5); cues.push(["shutter", t, 0.2]);
      } else if (it.line) {
        const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg"); svg.setAttribute("class", "str"); svg.setAttribute("viewBox", "0 0 1080 1920");
        const p = document.createElementNS("http://www.w3.org/2000/svg", "polyline"); p.setAttribute("points", it.line.join(" ")); p.setAttribute("class", it.cls || "rope");
        if (it.stroke) p.style.stroke = it.stroke; svg.appendChild(p); sec.appendChild(svg); e = null;
        const pts = []; for (let k = 0; k < it.line.length; k += 2) pts.push([it.line[k], it.line[k + 1]]);
        let len = 0; for (let k = 1; k < pts.length; k++) len += Math.hypot(pts[k][0] - pts[k - 1][0], pts[k][1] - pts[k - 1][1]); len = Math.ceil(len) + 2;
        const d = it.dur || 0.6;
        tl.fromTo(p, { attr: { "stroke-dasharray": len, "stroke-dashoffset": len } }, { attr: { "stroke-dashoffset": 0 }, duration: d, ease: "power2.inOut" }, t);
        if (it.pins) [pts[0], pts[pts.length - 1]].forEach((q, k) => { const pin = el("div", "pin", `left:${q[0]}px;top:${q[1]}px`); sec.appendChild(pin);
          tl.fromTo(pin, { opacity: 0, scale: 2.2 }, { opacity: 1, scale: 1, duration: 0.18, ease: "power3.in" }, k ? t + d : t - 0.1); });
        cues.push(["tap", t, 0.18]);
      } else if (it.card) {
        const g = el("div", "greenrip"), c = el("div", "card", "", `<div class="l1">${it.card[0]}</div><div class="l2">${it.card[1]}</div>`); sec.append(g, c);
        tl.fromTo(g, { opacity: 0, scale: 0.9, rotation: 3 }, { opacity: 1, scale: 1, rotation: 2, duration: 0.35, ease: "back.out(1.6)" }, t0 + 0.05);
        tl.fromTo(c, { opacity: 0 }, { opacity: 1, duration: 0.3 }, t0 + 0.05);
        tl.fromTo(c.children[0], { opacity: 0, y: 30 }, { opacity: 1, y: 0, duration: 0.3 }, t0 + 0.35);
        const t2 = it.at2 ? T(it.at2) - 0.1 : t0 + 1.2;
        tl.fromTo(c.children[1], { opacity: 0, scale: 1.6 }, { opacity: 1, scale: 1, duration: 0.3, ease: "power3.in" }, t2); tl.to(c.children[1], { scale: 1.06, duration: 2.5, ease: "none" }, t2 + 0.35); cues.push(["stamp", t2, 0.2]);
      } else {
        const kind = it.torn != null ? "torn" : it.big != null ? "big" : it.badge != null ? "badge" : it.bub != null ? "bub" : "stamp";
        const txt = it[kind];
        e = el("div", kind + " " + (it.cls || "") + (it.x == null ? " c" : ""), px(it), txt);
        if (kind === "stamp" && it.color) e.style.borderColor = it.color;
        if (kind === "badge" || kind === "bub") {
          tl.fromTo(e, { opacity: 0, scale: 0.2, rotation: rot - 20 }, { opacity: 1, scale: 1, rotation: rot, duration: 0.4, ease: "back.out(2.4)" }, t); cues.push(["pop", t, 0.2]);
        } else {
          tl.fromTo(e, { opacity: 0, scale: 1.6, rotation: rot }, { opacity: 1, scale: 1, rotation: rot, duration: 0.28, ease: "power3.in" }, t);
          cues.push([it.boom ? "boom" : "stamp", t + 0.1, 0.2]);
        }
        if (it.count != null) { const o = { v: 0 }, f = n => (it.pre || "") + Math.round(n).toLocaleString("en-US") + (it.post || "");
          tl.to(o, { v: it.count, duration: 1.1, ease: "power2.out", onUpdate: () => { e.innerHTML = f(o.v); } }, t); }
        if (it.dim) tl.to(e, { opacity: 0.35, duration: 0.25 }, T(it.dim));
        if (kind !== "big") float(e, t + 0.5, t1, 4);
      }
      if (e) { sec.appendChild(e);
        // ponytail: shrink-to-fit by measuring once (Kanit is embedded at render; preview may differ slightly)
        if (!it.pol && !it.badge && !it.sticker && !(it.cls || "").includes("q")) { const lim = 1040 - (it.x || 0), pw = e.style.width, keep = e.innerHTML; if (it.count != null) e.innerHTML = (it.pre || "") + it.count.toLocaleString("en-US") + (it.post || ""); e.style.width = "max-content"; const w = e.offsetWidth; e.style.width = pw; e.innerHTML = keep;
          if (w > lim) e.style.fontSize = (parseFloat(getComputedStyle(e).fontSize) * lim / w * 0.97) + "px"; } }
      if (it.punch) tl.to(sec, { scale: 1.04, duration: 0.12, yoyo: true, repeat: 1, ease: "power2.out", immediateRender: false }, t + 0.25);
      if (it.shake) tl.to(sec, { x: 12, yoyo: true, repeat: 5, duration: 0.05, immediateRender: false }, t + 0.3);
    });
  });
  const cv = document.getElementById("cover"); if (cv) tl.set(cv, { opacity: 0 }, 0.11);  // cover = first frame (FB/TikTok thumbnail)
  window.__CUES = cues;
  const master = gsap.timeline({ paused: true });
  master.add(tl.paused(false).timeScale(SPEED), 0);
  window.__timelines = window.__timelines || {}; window.__timelines["main"] = master;
})();
