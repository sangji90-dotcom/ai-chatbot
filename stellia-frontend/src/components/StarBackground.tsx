export default function StarBackground() {
  return (
    <>
      <div className="starfield">
        <div className="stars stars-1" />
        <div className="stars stars-2" />
        <div className="stars stars-3" />
        <div className="nebula nebula-primary" />
        <div className="nebula nebula-secondary" />
        <div className="nebula nebula-mystic" />
        <div className="vignette" />
      </div>
      <style>{`
        .starfield{
          position:fixed;
          inset:0;
          overflow:hidden;
          pointer-events:none;
          z-index:0;
          background:radial-gradient(circle at top,rgba(20,26,51,.65),var(--bg-base) 55%);
        }
        .stars{position:absolute;inset:-50%;animation:drift linear infinite;}
        .stars-1{opacity:.55;animation-duration:180s;background-image:radial-gradient(circle,rgba(255,255,255,.9) 1px,transparent 1.5px),radial-gradient(circle,rgba(255,255,255,.6) 1px,transparent 1.5px);background-size:180px 180px,260px 260px;background-position:0 0,80px 120px;}
        .stars-2{opacity:.3;animation-duration:240s;background-image:radial-gradient(circle,rgba(255,255,255,.8) 1px,transparent 1px),radial-gradient(circle,rgba(255,255,255,.4) 1px,transparent 1px);background-size:320px 320px,400px 400px;background-position:50px 100px,220px 180px;}
        .stars-3{opacity:.15;animation-duration:320s;background-image:radial-gradient(circle,rgba(255,255,255,.9) 1px,transparent 1px);background-size:500px 500px;}
        .nebula{position:absolute;border-radius:50%;filter:blur(90px);opacity:.22;mix-blend-mode:screen;}
        .nebula-primary{width:500px;height:500px;left:-120px;top:80px;background:var(--primary);animation:floatNebula 18s ease-in-out infinite;}
        .nebula-secondary{width:420px;height:420px;right:-100px;top:180px;background:var(--secondary);animation:floatNebula 22s ease-in-out infinite reverse;}
        .nebula-mystic{width:380px;height:380px;left:50%;bottom:-120px;transform:translateX(-50%);background:var(--mystic);animation:floatNebula 20s ease-in-out infinite;}
        .vignette{position:absolute;inset:0;background:radial-gradient(circle,transparent 45%,rgba(0,0,0,.45) 100%);}
        @keyframes drift{from{transform:translate3d(0,0,0)}to{transform:translate3d(-120px,-120px,0)}}
        @keyframes floatNebula{0%{transform:translate3d(0,0,0) scale(1)}50%{transform:translate3d(20px,-25px,0) scale(1.08)}100%{transform:translate3d(0,0,0) scale(1)}}
      `}</style>
    </>
  );
}