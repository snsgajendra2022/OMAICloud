/**
 * OM Human Presence — procedural 3D companion (Three.js).
 * Not MetaHuman yet — but a real 3D character body with eyes, jaw, head, glow.
 * Swap in a VRM/GLB later via OM_AVATAR_MODEL_URL.
 */
(function (global) {
  const Presence3D = {
    ready: false,
    speaking: false,
    presence: 'idle',
    mouth: 0,
    _lipFrames: null,
    _lipStart: 0,
    _raf: 0,
    _scene: null,
    _camera: null,
    _renderer: null,
    _avatar: null,
    _head: null,
    _jaw: null,
    _eyeL: null,
    _eyeR: null,
    _ring: null,
    _clock: null,
    _targetLook: { x: 0, y: 0 },

    async mount(container) {
      this._container = container;
      if (!global.THREE) {
        this.ready = true;
        this._mode = 'hud';
        this._startHudLoop();
        this._tryLoadThree(container);
        return true;
      }
      return this._mountThree(container);
    },

    _tryLoadThree(container) {
      if (this._threeLoading || global.THREE) return;
      this._threeLoading = true;
      const urls = [
        '/static/companion/three.min.js',
        'https://unpkg.com/three@0.160.0/build/three.min.js',
      ];
      const tryNext = (i) => {
        if (global.THREE) {
          this._mountThree(container);
          return;
        }
        if (i >= urls.length) return;
        const s = document.createElement('script');
        s.src = urls[i];
        s.async = true;
        s.onload = () => {
          if (global.THREE) this._mountThree(container);
          else tryNext(i + 1);
        };
        s.onerror = () => tryNext(i + 1);
        document.head.appendChild(s);
      };
      tryNext(0);
    },

    _startHudLoop() {
      if (this._raf) return;
      const loop = () => {
        this._raf = requestAnimationFrame(loop);
        this._emitMouth();
      };
      loop();
    },

    _emitMouth() {
      try {
        global.dispatchEvent(new CustomEvent('om-presence-mouth', {
          detail: { energy: this.mouth || 0, speaking: this.speaking },
        }));
      } catch (_) {}
    },

    _mountThree(container) {
      if (!global.THREE || !container) return false;
      const THREE = global.THREE;
      const w = container.clientWidth || 420;
      const h = container.clientHeight || 420;

      this._scene = new THREE.Scene();
      this._camera = new THREE.PerspectiveCamera(38, w / h, 0.1, 100);
      this._camera.position.set(0, 1.35, 3.2);

      this._renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
      this._renderer.setPixelRatio(Math.min(global.devicePixelRatio || 1, 2));
      this._renderer.setSize(w, h);
      this._renderer.setClearColor(0x000000, 0);
      container.innerHTML = '';
      container.appendChild(this._renderer.domElement);

      const key = new THREE.DirectionalLight(0xb8f4ff, 1.35);
      key.position.set(2, 4, 3);
      this._scene.add(key);
      const fill = new THREE.DirectionalLight(0xd4af37, 0.35);
      fill.position.set(-2, 1, -1);
      this._scene.add(fill);
      this._scene.add(new THREE.AmbientLight(0x1a3040, 0.55));

      const discGeo = new THREE.CircleGeometry(1.1, 64);
      const discMat = new THREE.MeshBasicMaterial({
        color: 0x75d5e3,
        transparent: true,
        opacity: 0.12,
      });
      const disc = new THREE.Mesh(discGeo, discMat);
      disc.rotation.x = -Math.PI / 2;
      disc.position.y = 0.02;
      this._scene.add(disc);

      this._avatar = new THREE.Group();
      this._buildBody(THREE);
      this._scene.add(this._avatar);

      const ringGeo = new THREE.TorusGeometry(1.35, 0.015, 8, 100);
      const ringMat = new THREE.MeshBasicMaterial({
        color: 0x75d5e3,
        transparent: true,
        opacity: 0.55,
      });
      this._ring = new THREE.Mesh(ringGeo, ringMat);
      this._ring.position.y = 1.25;
      this._scene.add(this._ring);

      this._clock = new THREE.Clock();
      this._mode = '3d';
      this.ready = true;
      if (!this._raf) {
        const loop = () => {
          this._raf = requestAnimationFrame(loop);
          this._tick();
        };
        loop();
      }

      global.addEventListener('resize', () => {
        if (!container.isConnected) return;
        const ww = container.clientWidth || 420;
        const hh = container.clientHeight || 420;
        this._camera.aspect = ww / hh;
        this._camera.updateProjectionMatrix();
        this._renderer.setSize(ww, hh);
      });
      return true;
    },

    _buildBody(THREE) {
      const skin = new THREE.MeshStandardMaterial({
        color: 0x0e2433,
        metalness: 0.55,
        roughness: 0.35,
        emissive: 0x0a3048,
        emissiveIntensity: 0.35,
      });
      const cyan = new THREE.MeshStandardMaterial({
        color: 0x75d5e3,
        emissive: 0x75d5e3,
        emissiveIntensity: 0.85,
        metalness: 0.4,
        roughness: 0.25,
      });
      const gold = new THREE.MeshStandardMaterial({
        color: 0xd4af37,
        emissive: 0xd4af37,
        emissiveIntensity: 0.4,
        metalness: 0.6,
        roughness: 0.3,
      });

      // Torso
      const torso = new THREE.Mesh(new THREE.CapsuleGeometry(0.38, 0.7, 8, 16), skin);
      torso.position.y = 0.95;
      this._avatar.add(torso);

      // Shoulders
      const shoulder = new THREE.Mesh(new THREE.CapsuleGeometry(0.12, 0.55, 6, 10), skin);
      shoulder.rotation.z = Math.PI / 2;
      shoulder.position.set(0, 1.35, 0);
      this._avatar.add(shoulder);

      // Head group
      this._head = new THREE.Group();
      this._head.position.y = 1.72;
      const skull = new THREE.Mesh(new THREE.SphereGeometry(0.28, 32, 32), skin);
      this._head.add(skull);

      // Visor / face plate
      const visor = new THREE.Mesh(
        new THREE.SphereGeometry(0.265, 32, 16, 0, Math.PI * 2, 0, Math.PI * 0.45),
        new THREE.MeshStandardMaterial({
          color: 0x041018,
          metalness: 0.8,
          roughness: 0.2,
          transparent: true,
          opacity: 0.85,
        })
      );
      visor.rotation.x = Math.PI;
      visor.position.z = 0.02;
      this._head.add(visor);

      // Eyes
      this._eyeL = new THREE.Mesh(new THREE.SphereGeometry(0.035, 16, 16), cyan);
      this._eyeR = this._eyeL.clone();
      this._eyeL.position.set(-0.08, 0.04, 0.22);
      this._eyeR.position.set(0.08, 0.04, 0.22);
      this._head.add(this._eyeL);
      this._head.add(this._eyeR);

      // Jaw (lip sync)
      this._jaw = new THREE.Mesh(new THREE.BoxGeometry(0.16, 0.04, 0.08), gold);
      this._jaw.position.set(0, -0.12, 0.2);
      this._head.add(this._jaw);

      // Chest core light
      const core = new THREE.Mesh(new THREE.SphereGeometry(0.09, 16, 16), cyan);
      core.position.set(0, 1.05, 0.32);
      this._avatar.add(core);
      this._core = core;

      // Arms — gesture presence (not a static bust)
      this._armL = new THREE.Group();
      this._armR = new THREE.Group();
      const upperL = new THREE.Mesh(new THREE.CapsuleGeometry(0.07, 0.42, 6, 10), skin);
      upperL.position.y = -0.28;
      this._armL.add(upperL);
      const upperR = upperL.clone();
      this._armR.add(upperR);
      this._armL.position.set(-0.48, 1.32, 0);
      this._armR.position.set(0.48, 1.32, 0);
      this._armL.rotation.z = 0.35;
      this._armR.rotation.z = -0.35;
      this._avatar.add(this._armL);
      this._avatar.add(this._armR);

      // Hip / legs hint for full-body read
      const hip = new THREE.Mesh(new THREE.CapsuleGeometry(0.32, 0.15, 6, 12), skin);
      hip.position.y = 0.48;
      this._avatar.add(hip);
      const legL = new THREE.Mesh(new THREE.CapsuleGeometry(0.1, 0.55, 6, 10), skin);
      const legR = legL.clone();
      legL.position.set(-0.14, 0.12, 0);
      legR.position.set(0.14, 0.12, 0);
      this._avatar.add(legL);
      this._avatar.add(legR);

      this._avatar.add(this._head);
    },

    setPresence(mode) {
      this.presence = String(mode || 'idle').toLowerCase();
    },

    setSpeaking(on, energy) {
      this.speaking = !!on;
      if (typeof energy === 'number') this.mouth = energy;
      if (!on) {
        this._lipFrames = null;
        this.mouth = 0;
      }
    },

    /** Apply server om_avatar / avatar pack (animation, face, gesture, lips). */
    applyAvatarState(pack) {
      if (!pack || typeof pack !== 'object') return;
      const mode =
        pack.presence ||
        pack.mode ||
        pack.state ||
        pack.animation ||
        (pack.expression && pack.expression.presence) ||
        '';
      if (mode) this.setPresence(mode);
      const face = pack.face || pack.expression || {};
      if (face && typeof face === 'object') {
        const mood = String(face.mood || face.label || face.emotion || '').toLowerCase();
        if (mood && !mode) this.setPresence(mood);
      }
      const lips = pack.lips || pack.lip_plan || pack.visemes;
      if (lips) this.applyLipPlan(lips);
      const gest = String(pack.gesture || pack.pose || '').toLowerCase();
      if (gest === 'wave' || gest === 'point') this.presence = 'attentive';
      if (pack.speaking === true) this.speaking = true;
      if (pack.speaking === false) this.setSpeaking(false, 0);
    },

    /** STEP 4 — drive jaw from viseme plan ({ frames: [{t,jaw}] }) */
    applyLipPlan(lips) {
      this._lipFrames = (lips && lips.frames) ? lips.frames : null;
      this._lipStart = (typeof performance !== 'undefined' ? performance.now() : Date.now());
      this.speaking = true;
      this.presence = 'speaking';
    },

    setMouth(energy) {
      this.mouth = Math.max(0, Math.min(1, Number(energy) || 0));
      this._emitMouth();
    },

    _tick() {
      if (!this.ready) return;
      if (!this._clock || !this._scene) {
        this._emitMouth();
        return;
      }
      const t = this._clock.getElapsedTime();
      const p = this.presence;

      // Idle breath
      let breath = Math.sin(t * 1.4) * 0.012;
      let headY = Math.sin(t * 0.7) * 0.04;
      let headX = Math.sin(t * 0.45) * 0.03;
      let glow = 0.55;

      if (p === 'attentive' || p === 'silent_listening') {
        headY *= 0.3;
        headX = 0.02;
        glow = 0.75;
      } else if (p === 'thinking' || p === 'remembering') {
        headY = Math.sin(t * 0.35) * 0.06;
        glow = 0.5;
      } else if (p === 'concerned') {
        headX = -0.05;
        glow = 0.45;
      } else if (p === 'excited') {
        breath *= 1.6;
        glow = 0.95;
      } else if (p === 'speaking') {
        glow = 0.9;
      }

      if (this._avatar) {
        this._avatar.position.y = breath;
        this._avatar.rotation.y = Math.sin(t * 0.22) * 0.06;
      }
      if (this._head) {
        this._head.rotation.y = headY;
        this._head.rotation.x = headX;
      }
      if (this._armL && this._armR) {
        const swing = Math.sin(t * 1.1) * 0.08;
        this._armL.rotation.x = swing + (this.speaking ? 0.15 : 0);
        this._armR.rotation.x = -swing + (this.speaking ? 0.12 : 0);
        if (p === 'attentive') {
          this._armL.rotation.z = 0.55;
          this._armR.rotation.z = -0.25;
        } else {
          this._armL.rotation.z = 0.35;
          this._armR.rotation.z = -0.35;
        }
      }
      if (this._ring) {
        this._ring.rotation.z = t * 0.25;
        this._ring.rotation.x = Math.sin(t * 0.2) * 0.2;
      }

      // STEP 4 — Lip sync (viseme frames + live audio energy)
      let mouth = 0.02;
      if (this.speaking) {
        if (this._lipFrames && this._lipFrames.length) {
          const elapsed = ((typeof performance !== 'undefined' ? performance.now() : Date.now()) - this._lipStart) / 1000;
          let cur = this._lipFrames[0];
          for (let i = 0; i < this._lipFrames.length; i++) {
            const f = this._lipFrames[i];
            if ((f.t || 0) <= elapsed) cur = f;
            else break;
          }
          mouth = Number(cur.jaw || cur.mouth || 0.08);
          mouth = mouth * 0.65 + (this.mouth || 0) * 0.35;
        } else {
          mouth = 0.04 + Math.abs(Math.sin(t * 14)) * 0.09 + (this.mouth || 0) * 0.22;
        }
      }
      if (this._jaw) {
        this._jaw.scale.y = 1 + mouth * 8;
        this._jaw.position.y = -0.12 - mouth * 0.5;
      }
      if (this._eyeL && this._eyeR) {
        const blink = Math.sin(t * 0.8) > 0.96 ? 0.15 : 1;
        this._eyeL.scale.y = blink;
        this._eyeR.scale.y = blink;
        const em = this._eyeL.material;
        if (em && em.emissiveIntensity != null) {
          em.emissiveIntensity = glow;
          this._eyeR.material.emissiveIntensity = glow;
        }
      }
      if (this._core && this._core.material) {
        this._core.material.emissiveIntensity = glow * (this.speaking ? 1.3 : 1);
      }

      if (this._renderer && this._scene && this._camera) {
        this._renderer.render(this._scene, this._camera);
      }
      this._emitMouth();
    },

    dispose() {
      cancelAnimationFrame(this._raf);
      this.ready = false;
    },
  };

  global.OMPresence3D = Presence3D;
})(typeof window !== 'undefined' ? window : globalThis);
