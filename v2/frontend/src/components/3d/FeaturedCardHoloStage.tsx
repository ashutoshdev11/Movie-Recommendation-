import React, { useEffect, useRef } from 'react';
import * as THREE from 'three';

interface FeaturedCardHoloStageProps {
  className?: string;
}

export const FeaturedCardHoloStage: React.FC<FeaturedCardHoloStageProps> = ({ className = '' }) => {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    // 1. Scene, Camera, Renderer
    const scene = new THREE.Scene();

    const width = container.clientWidth || 500;
    const height = container.clientHeight || 450;

    const camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 1000);
    camera.position.set(0, 0, 36);

    const renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true });
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.setSize(width, height);
    renderer.setClearColor(0x000000, 0);
    container.appendChild(renderer.domElement);

    // Group for parallax rotation
    const holoGroup = new THREE.Group();
    scene.add(holoGroup);

    // 2. Lighting
    const cyanLight = new THREE.PointLight(0x00f2fe, 3, 60);
    cyanLight.position.set(-18, 8, 12);
    scene.add(cyanLight);

    const magentaLight = new THREE.PointLight(0xff2a85, 3, 60);
    magentaLight.position.set(18, -8, 12);
    scene.add(magentaLight);

    const ambientLight = new THREE.AmbientLight(0xffffff, 0.6);
    scene.add(ambientLight);

    // 3. Left Folded Glass Prism (Cyan / Blue Neon)
    // Modeled as a multi-faceted geometric ribbon framing the left of the card
    const leftGeo = new THREE.CylinderGeometry(7, 9, 16, 5, 1, false);
    const leftMat = new THREE.MeshStandardMaterial({
      color: 0x00f2fe,
      roughness: 0.15,
      metalness: 0.6,
      transparent: true,
      opacity: 0.38,
      side: THREE.DoubleSide,
      depthWrite: false,
    });
    const leftMesh = new THREE.Mesh(leftGeo, leftMat);
    leftMesh.position.set(-18, -1, -6);
    leftMesh.rotation.set(0.3, 0.4, -0.2);

    const leftEdges = new THREE.EdgesGeometry(leftGeo);
    const leftLineMat = new THREE.LineBasicMaterial({
      color: 0x00f2fe,
      transparent: true,
      opacity: 0.9,
    });
    const leftLines = new THREE.LineSegments(leftEdges, leftLineMat);
    leftMesh.add(leftLines);
    holoGroup.add(leftMesh);

    // 4. Right Folded Glass Prism (Violet / Magenta Neon)
    // Modeled as a multi-faceted geometric ribbon framing the right of the card
    const rightGeo = new THREE.CylinderGeometry(6, 8, 15, 6, 1, false);
    const rightMat = new THREE.MeshStandardMaterial({
      color: 0xb829dd,
      roughness: 0.15,
      metalness: 0.6,
      transparent: true,
      opacity: 0.38,
      side: THREE.DoubleSide,
      depthWrite: false,
    });
    const rightMesh = new THREE.Mesh(rightGeo, rightMat);
    rightMesh.position.set(18, 2, -6);
    rightMesh.rotation.set(-0.3, -0.5, 0.2);

    const rightEdges = new THREE.EdgesGeometry(rightGeo);
    const rightLineMat = new THREE.LineBasicMaterial({
      color: 0xff2a85,
      transparent: true,
      opacity: 0.95,
    });
    const rightLines = new THREE.LineSegments(rightEdges, rightLineMat);
    rightMesh.add(rightLines);
    holoGroup.add(rightMesh);

    // 5. Bottom Holographic Pedestal
    const pedestalGeo = new THREE.TorusGeometry(15, 0.35, 16, 64);
    const pedestalMat = new THREE.MeshBasicMaterial({
      color: 0x00f2fe,
      transparent: true,
      opacity: 0.6,
      wireframe: true,
    });
    const pedestal = new THREE.Mesh(pedestalGeo, pedestalMat);
    pedestal.position.set(0, -13, -5);
    pedestal.rotation.x = Math.PI / 2.3;
    holoGroup.add(pedestal);

    // Inner glowing ring
    const innerRingGeo = new THREE.RingGeometry(8, 11, 32);
    const innerRingMat = new THREE.MeshBasicMaterial({
      color: 0xb829dd,
      transparent: true,
      opacity: 0.35,
      side: THREE.DoubleSide,
    });
    const innerRing = new THREE.Mesh(innerRingGeo, innerRingMat);
    innerRing.position.set(0, -13.2, -5.2);
    innerRing.rotation.x = Math.PI / 2.3;
    holoGroup.add(innerRing);

    // 6. Floating Digital Pixel Particles (Cyan, Magenta, Violet Cubes)
    // Matches the glowing floating pixel blocks in the reference image
    const particleCount = 26;
    const boxGeo = new THREE.BoxGeometry(0.7, 0.7, 0.7);
    const boxColors = [0x00f2fe, 0xff2a85, 0xb829dd, 0x38bdf8];

    const particles: {
      mesh: THREE.Mesh;
      baseX: number;
      baseY: number;
      baseZ: number;
      speed: number;
      offset: number;
    }[] = [];

    for (let i = 0; i < particleCount; i++) {
      const col = boxColors[i % boxColors.length];
      const bMat = new THREE.MeshBasicMaterial({
        color: col,
        transparent: true,
        opacity: 0.85,
      });
      const bMesh = new THREE.Mesh(boxGeo, bMat);

      // Position along perimeter of card (not directly in front of the center)
      const side = Math.random() > 0.5 ? 1 : -1;
      const baseX = side * (14 + Math.random() * 12);
      const baseY = (Math.random() - 0.5) * 26;
      const baseZ = -2 - Math.random() * 8;

      bMesh.position.set(baseX, baseY, baseZ);
      bMesh.rotation.set(Math.random() * Math.PI, Math.random() * Math.PI, 0);

      holoGroup.add(bMesh);
      particles.push({
        mesh: bMesh,
        baseX,
        baseY,
        baseZ,
        speed: 0.4 + Math.random() * 0.6,
        offset: Math.random() * Math.PI * 2,
      });
    }

    // 7. Mouse Parallax Handler
    let mouseX = 0;
    let mouseY = 0;
    let targetX = 0;
    let targetY = 0;

    const handleMouseMove = (e: MouseEvent) => {
      const rect = container.getBoundingClientRect();
      const x = (e.clientX - rect.left) / rect.width - 0.5;
      const y = (e.clientY - rect.top) / rect.height - 0.5;
      targetX = x * 0.15;
      targetY = -y * 0.15;
    };

    window.addEventListener('mousemove', handleMouseMove);

    // 8. Animation Loop
    let animId: number;
    const clock = new THREE.Clock();

    const animate = () => {
      animId = requestAnimationFrame(animate);
      const elapsed = clock.getElapsedTime();

      if (!prefersReducedMotion) {
        // Slow majestic rotation of glass prisms
        leftMesh.rotation.y = 0.4 + Math.sin(elapsed * 0.4) * 0.15;
        leftMesh.rotation.x = 0.3 + Math.cos(elapsed * 0.3) * 0.1;
        leftMesh.position.y = -1 + Math.sin(elapsed * 0.8) * 0.5;

        rightMesh.rotation.y = -0.5 + Math.cos(elapsed * 0.4) * 0.15;
        rightMesh.rotation.x = -0.3 + Math.sin(elapsed * 0.3) * 0.1;
        rightMesh.position.y = 2 + Math.cos(elapsed * 0.7) * 0.5;

        pedestal.rotation.z = elapsed * 0.1;
        innerRing.rotation.z = -elapsed * 0.15;

        // Floating particle oscillation
        particles.forEach((p) => {
          p.mesh.position.y = p.baseY + Math.sin(elapsed * p.speed + p.offset) * 1.2;
          p.mesh.rotation.x += 0.01;
          p.mesh.rotation.y += 0.015;
        });

        // Smooth mouse damping
        mouseX += (targetX - mouseX) * 0.08;
        mouseY += (targetY - mouseY) * 0.08;
        holoGroup.rotation.y = mouseX;
        holoGroup.rotation.x = mouseY;
      }

      renderer.render(scene, camera);
    };

    animate();

    // 9. Resize Handler
    const handleResize = () => {
      if (!container) return;
      const w = container.clientWidth || 500;
      const h = container.clientHeight || 450;
      camera.aspect = w / h;
      camera.updateProjectionMatrix();
      renderer.setSize(w, h);
    };

    window.addEventListener('resize', handleResize);

    return () => {
      cancelAnimationFrame(animId);
      window.removeEventListener('mousemove', handleMouseMove);
      window.removeEventListener('resize', handleResize);

      if (container.contains(renderer.domElement)) {
        container.removeChild(renderer.domElement);
      }

      // Dispose Three.js objects
      leftGeo.dispose();
      leftMat.dispose();
      leftEdges.dispose();
      leftLineMat.dispose();

      rightGeo.dispose();
      rightMat.dispose();
      rightEdges.dispose();
      rightLineMat.dispose();

      pedestalGeo.dispose();
      pedestalMat.dispose();
      innerRingGeo.dispose();
      innerRingMat.dispose();

      boxGeo.dispose();
      renderer.dispose();
    };
  }, []);

  return (
    <div
      ref={containerRef}
      className={`w-full h-full pointer-events-none ${className}`}
      style={{ overflow: 'visible' }}
    />
  );
};
