/**
 * 3D Interactive Bookshelf using Three.js
 * prakashsellathurai.com
 */

(function () {
  'use strict';

  // Check if WebGL is supported
  function isWebGLSupported() {
    try {
      var canvas = document.createElement('canvas');
      return !!(
        window.WebGLRenderingContext &&
        (canvas.getContext('webgl') || canvas.getContext('experimental-webgl'))
      );
    } catch (e) {
      return false;
    }
  }

  var container = document.getElementById('bookshelf-3d-canvas');
  var wrapper3D = document.getElementById('bookshelf-3d-wrapper');
  var container2D = document.getElementById('bookshelf-2d-container');
  var btn3D = document.getElementById('view-3d-btn');
  var btn2D = document.getElementById('view-2d-btn');
  var resetCamBtn = document.getElementById('reset-cam-btn');
  var searchInput = document.getElementById('bookshelf-search');
  var filterChips = document.querySelectorAll('.filter-chip');

  // Modal elements
  var modal = document.getElementById('book-detail-modal');
  var modalBackdrop = modal ? modal.querySelector('.book-detail-backdrop') : null;
  var modalClose = modal ? modal.querySelector('.book-detail-close') : null;
  var modalCover = document.getElementById('modal-book-cover');
  var modalCategory = document.getElementById('modal-book-category');
  var modalTitle = document.getElementById('modal-book-title');
  var modalAuthor = document.getElementById('modal-book-author');
  var modalRating = document.getElementById('modal-book-rating');
  var modalDesc = document.getElementById('modal-book-desc');
  var modalLink = document.getElementById('modal-book-link');

  // Read data from script tag
  var rawDataEl = document.getElementById('bookshelf-data');
  var categoriesData = [];
  if (rawDataEl && rawDataEl.textContent) {
    try {
      categoriesData = JSON.parse(rawDataEl.textContent);
    } catch (err) {
      console.warn('Failed to parse bookshelf data JSON', err);
    }
  }

  // Fallback to 2D view if WebGL or Three.js is not present
  if (!isWebGLSupported() || typeof THREE === 'undefined') {
    if (wrapper3D) wrapper3D.classList.add('hidden');
    if (container2D) container2D.classList.remove('hidden');
    if (btn3D) btn3D.style.display = 'none';
    if (btn2D) btn2D.classList.add('active');
    return;
  }

  // --- View Toggle ---
  function setView(mode) {
    if (mode === '2d') {
      wrapper3D.classList.add('hidden');
      container2D.classList.remove('hidden');
      btn2D.classList.add('active');
      btn2D.setAttribute('aria-pressed', 'true');
      btn3D.classList.remove('active');
      btn3D.setAttribute('aria-pressed', 'false');
    } else {
      container2D.classList.add('hidden');
      wrapper3D.classList.remove('hidden');
      btn3D.classList.add('active');
      btn3D.setAttribute('aria-pressed', 'true');
      btn2D.classList.remove('active');
      btn2D.setAttribute('aria-pressed', 'false');
      onWindowResize();
    }
  }

  if (btn3D) btn3D.addEventListener('click', function () { setView('3d'); });
  if (btn2D) btn2D.addEventListener('click', function () { setView('2d'); });

  // --- Three.js Setup ---
  var scene, camera, renderer, controls;
  var raycaster = new THREE.Raycaster();
  var mouse = new THREE.Vector2(-9999, -9999);
  var bookMeshes = [];
  var hoveredBook = null;
  var selectedBook = null;
  var currentFilter = 'all';
  var searchQuery = '';

  // Palette generator for procedural covers
  var coverPalettes = [
    { bg: '#2b3a42', fg: '#f0f3f4', accent: '#e06d53' },
    { bg: '#3f2b42', fg: '#f5eff7', accent: '#c99e5a' },
    { bg: '#1c3144', fg: '#d00000', accent: '#f0caa3' },
    { bg: '#2d3a3a', fg: '#e8ecef', accent: '#70a9a1' },
    { bg: '#4a2511', fg: '#ffdfba', accent: '#ffb347' },
    { bg: '#1e3d2f', fg: '#e8f5e9', accent: '#a5d6a7' },
    { bg: '#36302e', fg: '#f5ede0', accent: '#d4a373' },
    { bg: '#2b2d42', fg: '#edf2f4', accent: '#ef233c' }
  ];

  function getPaletteForBook(title) {
    var hash = 0;
    for (var i = 0; i < title.length; i++) {
      hash = (hash * 31 + title.charCodeAt(i)) & 0xffffffff;
    }
    var idx = Math.abs(hash) % coverPalettes.length;
    return coverPalettes[idx];
  }

  function createBookCoverCanvas(book) {
    var canvas = document.createElement('canvas');
    canvas.width = 512;
    canvas.height = 768;
    var ctx = canvas.getContext('2d');
    var pal = getPaletteForBook(book.title);

    // Background gradient
    var grad = ctx.createLinearGradient(0, 0, 512, 768);
    grad.addColorStop(0, pal.bg);
    grad.addColorStop(1, '#111416');
    ctx.fillStyle = grad;
    ctx.fillRect(0, 0, 512, 768);

    // Subtle texture border
    ctx.strokeStyle = pal.accent;
    ctx.lineWidth = 12;
    ctx.strokeRect(24, 24, 464, 720);

    ctx.strokeStyle = 'rgba(255,255,255,0.15)';
    ctx.lineWidth = 2;
    ctx.strokeRect(36, 36, 440, 696);

    // Spine edge highlight
    var spineShade = ctx.createLinearGradient(0, 0, 60, 0);
    spineShade.addColorStop(0, 'rgba(0,0,0,0.6)');
    spineShade.addColorStop(1, 'rgba(0,0,0,0)');
    ctx.fillStyle = spineShade;
    ctx.fillRect(0, 0, 60, 768);

    // Title
    ctx.fillStyle = pal.fg;
    ctx.font = 'bold 38px Georgia, serif';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';

    var words = (book.title || 'Untitled').split(' ');
    var lines = [];
    var curLine = '';
    for (var i = 0; i < words.length; i++) {
      var testLine = curLine ? curLine + ' ' + words[i] : words[i];
      if (ctx.measureText(testLine).width > 400 && curLine) {
        lines.push(curLine);
        curLine = words[i];
      } else {
        curLine = testLine;
      }
    }
    if (curLine) lines.push(curLine);

    var startY = 300 - (lines.length - 1) * 25;
    for (var j = 0; j < lines.length && j < 6; j++) {
      ctx.fillText(lines[j], 256, startY + j * 48);
    }

    // Author
    ctx.fillStyle = pal.accent;
    ctx.font = 'italic 26px sans-serif';
    ctx.fillText(book.author || 'Unknown', 256, 560);

    // Category / Star tag
    if (book.rating && book.rating !== '0') {
      var stars = '★'.repeat(parseInt(book.rating, 10));
      ctx.fillStyle = '#f5c518';
      ctx.font = '28px sans-serif';
      ctx.fillText(stars, 256, 620);
    }

    return canvas;
  }

  function createBookSpineCanvas(book) {
    var canvas = document.createElement('canvas');
    canvas.width = 128;
    canvas.height = 768;
    var ctx = canvas.getContext('2d');
    var pal = getPaletteForBook(book.title);

    ctx.fillStyle = pal.bg;
    ctx.fillRect(0, 0, 128, 768);

    // Spine accents
    ctx.fillStyle = pal.accent;
    ctx.fillRect(10, 30, 108, 6);
    ctx.fillRect(10, 732, 108, 6);

    // Rotated Title Text
    ctx.save();
    ctx.translate(64, 384);
    ctx.rotate(Math.PI / 2);
    ctx.fillStyle = pal.fg;
    ctx.font = 'bold 24px Georgia, serif';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';

    var displayTitle = book.title || '';
    if (displayTitle.length > 32) {
      displayTitle = displayTitle.slice(0, 30) + '...';
    }
    ctx.fillText(displayTitle, 0, 0);
    ctx.restore();

    return canvas;
  }

  // --- Initialize Three.js ---
  var textureLoader = new THREE.TextureLoader();
  var defaultCamPos = { x: 0, y: 1.5, z: 22 };
  var defaultTarget = { x: 0, y: 1.5, z: 0 };
  var targetCamPos = { x: defaultCamPos.x, y: defaultCamPos.y, z: defaultCamPos.z };
  var targetLookAt = { x: defaultTarget.x, y: defaultTarget.y, z: defaultTarget.z };

  function initThree() {
    var width = container.clientWidth || 900;
    var height = 580;

    scene = new THREE.Scene();

    camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 1000);
    camera.position.set(defaultCamPos.x, defaultCamPos.y, defaultCamPos.z);

    renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setSize(width, height);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.shadowMap.enabled = true;
    renderer.shadowMap.type = THREE.PCFSoftShadowMap;
    container.appendChild(renderer.domElement);

    // Orbit Controls
    controls = new THREE.OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.dampingFactor = 0.06;
    controls.minDistance = 6;
    controls.maxDistance = 38;
    controls.minPolarAngle = Math.PI / 6;
    controls.maxPolarAngle = Math.PI / 2 + 0.05;
    controls.minAzimuthAngle = -Math.PI / 2.2;
    controls.maxAzimuthAngle = Math.PI / 2.2;
    controls.target.set(defaultTarget.x, defaultTarget.y, defaultTarget.z);

    setupLighting();
    buildBookcaseAndBooks();
    updateThemeColors();

    // Event listeners
    container.addEventListener('mousemove', onMouseMove, false);
    container.addEventListener('click', onCanvasClick, false);
    container.addEventListener('mouseleave', onMouseLeave, false);
    window.addEventListener('resize', onWindowResize, false);

    // Theme observer
    var observer = new MutationObserver(function () {
      updateThemeColors();
    });
    observer.observe(document.documentElement, {
      attributes: true,
      attributeFilter: ['data-theme', 'class']
    });

    animate();
  }

  var ambientLight, dirLight, pointLight;

  function setupLighting() {
    ambientLight = new THREE.AmbientLight(0xfff5e6, 0.85);
    scene.add(ambientLight);

    dirLight = new THREE.DirectionalLight(0xffffff, 0.95);
    dirLight.position.set(10, 18, 15);
    dirLight.castShadow = true;
    dirLight.shadow.mapSize.width = 1024;
    dirLight.shadow.mapSize.height = 1024;
    dirLight.shadow.camera.near = 0.5;
    dirLight.shadow.camera.far = 50;
    dirLight.shadow.bias = -0.001;
    scene.add(dirLight);

    pointLight = new THREE.PointLight(0xffd1a4, 0.5, 30);
    pointLight.position.set(-6, 8, 10);
    scene.add(pointLight);
  }

  function updateThemeColors() {
    var isDark = document.documentElement.getAttribute('data-theme') === 'dark';
    if (isDark) {
      if (ambientLight) ambientLight.color.setHex(0xdedede);
      if (pointLight) pointLight.color.setHex(0x5c80a6);
      scene.fog = new THREE.FogExp2(0x161719, 0.012);
    } else {
      if (ambientLight) ambientLight.color.setHex(0xfff7ed);
      if (pointLight) pointLight.color.setHex(0xffd1a4);
      scene.fog = new THREE.FogExp2(0xf8f6f0, 0.008);
    }
  }

  // --- Bookcase & Books Construction ---
  function buildBookcaseAndBooks() {
    var woodColor = 0x5a3e2b;
    var woodBackdropColor = 0x3d2719;

    var woodMat = new THREE.MeshStandardMaterial({
      color: woodColor,
      roughness: 0.65,
      metalness: 0.1
    });

    var backMat = new THREE.MeshStandardMaterial({
      color: woodBackdropColor,
      roughness: 0.8,
      metalness: 0.05
    });

    var pageMat = new THREE.MeshStandardMaterial({
      color: 0xf3ede2,
      roughness: 0.9,
      metalness: 0.0
    });

    var shelfWidth = 26;
    var shelfDepth = 3.2;
    var shelfThick = 0.45;
    var shelfSpacing = 3.8;
    var numShelves = Math.max(categoriesData.length, 3);
    var bookcaseHeight = numShelves * shelfSpacing + 1.2;

    // Outer Backboard
    var backGeo = new THREE.BoxGeometry(shelfWidth + 0.8, bookcaseHeight, 0.4);
    var backMesh = new THREE.Mesh(backGeo, backMat);
    backMesh.position.set(0, (bookcaseHeight / 2) - 1.5, -shelfDepth / 2 - 0.2);
    backMesh.receiveShadow = true;
    scene.add(backMesh);

    // Left and Right Wall
    var wallGeo = new THREE.BoxGeometry(shelfThick, bookcaseHeight, shelfDepth);
    var leftWall = new THREE.Mesh(wallGeo, woodMat);
    leftWall.position.set(-(shelfWidth / 2) - (shelfThick / 2), (bookcaseHeight / 2) - 1.5, 0);
    leftWall.castShadow = true;
    leftWall.receiveShadow = true;
    scene.add(leftWall);

    var rightWall = new THREE.Mesh(wallGeo, woodMat);
    rightWall.position.set((shelfWidth / 2) + (shelfThick / 2), (bookcaseHeight / 2) - 1.5, 0);
    rightWall.castShadow = true;
    rightWall.receiveShadow = true;
    scene.add(rightWall);

    // Top and Bottom Boards
    var topBoard = new THREE.Mesh(new THREE.BoxGeometry(shelfWidth + shelfThick * 2 + 0.4, shelfThick + 0.2, shelfDepth + 0.3), woodMat);
    topBoard.position.set(0, bookcaseHeight - 1.5, 0.1);
    topBoard.castShadow = true;
    scene.add(topBoard);

    var botBoard = new THREE.Mesh(new THREE.BoxGeometry(shelfWidth + shelfThick * 2 + 0.4, shelfThick + 0.2, shelfDepth + 0.3), woodMat);
    botBoard.position.set(0, -1.5, 0.1);
    botBoard.receiveShadow = true;
    scene.add(botBoard);

    // Build each Shelf Tier
    for (var s = 0; s < numShelves; s++) {
      var shelfY = s * shelfSpacing - 1.5;

      // Shelf board
      var shelfGeo = new THREE.BoxGeometry(shelfWidth, shelfThick, shelfDepth);
      var shelfMesh = new THREE.Mesh(shelfGeo, woodMat);
      shelfMesh.position.set(0, shelfY, 0);
      shelfMesh.receiveShadow = true;
      shelfMesh.castShadow = true;
      scene.add(shelfMesh);

      // Shelf Plaque / Label
      if (categoriesData[s]) {
        var group = categoriesData[s];
        createShelfLabelMesh(group.label, shelfY + (shelfThick / 2) + 0.15, -(shelfWidth / 2) + 0.8, -shelfDepth / 2 + 0.3);

        // Populate books on this shelf
        populateBooksOnShelf(group, shelfY + (shelfThick / 2), shelfWidth - 2.5, pageMat);
      }
    }
  }

  function createShelfLabelMesh(text, y, x, z) {
    var canvas = document.createElement('canvas');
    canvas.width = 512;
    canvas.height = 128;
    var ctx = canvas.getContext('2d');

    ctx.fillStyle = '#b0563c';
    ctx.roundRect ? ctx.roundRect(10, 10, 492, 108, 16) : ctx.rect(10, 10, 492, 108);
    ctx.fill();

    ctx.strokeStyle = '#e2dec5';
    ctx.lineWidth = 6;
    ctx.stroke();

    ctx.fillStyle = '#ffffff';
    ctx.font = 'bold 44px sans-serif';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText(text.toUpperCase(), 256, 64);

    var labelTex = new THREE.CanvasTexture(canvas);
    var labelMat = new THREE.MeshBasicMaterial({ map: labelTex, transparent: true });
    var labelGeo = new THREE.PlaneGeometry(2.8, 0.7);
    var labelMesh = new THREE.Mesh(labelGeo, labelMat);
    labelMesh.position.set(x + 1.2, y + 2.9, z + 0.1);
    scene.add(labelMesh);
  }

  function populateBooksOnShelf(group, shelfY, availableWidth, pageMat) {
    var books = group.books || [];
    if (!books.length) return;

    var startX = -(availableWidth / 2) + 0.8;
    var curX = startX;

    for (var i = 0; i < books.length; i++) {
      var book = books[i];

      // Realistic book geometry sizing
      var bookW = 1.45 + (Math.sin(i * 99) * 0.12);
      var bookH = 2.15 + (Math.cos(i * 77) * 0.2);
      var bookD = 0.38 + ((i % 3) * 0.08);

      if (curX + bookW > (availableWidth / 2) + 0.5) {
        // Space limit on one shelf tier
        break;
      }

      var spineCanvas = createBookSpineCanvas(book);
      var spineTex = new THREE.CanvasTexture(spineCanvas);

      var coverCanvas = createBookCoverCanvas(book);
      var coverTex = new THREE.CanvasTexture(coverCanvas);

      // Materials: [Right(+X), Left(-X), Top(+Y), Bottom(-Y), Front(+Z), Back(-Z)]
      var coverMat = new THREE.MeshStandardMaterial({
        map: coverTex,
        roughness: 0.4,
        metalness: 0.05
      });

      var spineMat = new THREE.MeshStandardMaterial({
        map: spineTex,
        roughness: 0.5,
        metalness: 0.05
      });

      var backCoverMat = new THREE.MeshStandardMaterial({
        color: getPaletteForBook(book.title).bg,
        roughness: 0.6,
        metalness: 0.05
      });

      var mats = [
        pageMat,     // +X right (page edges)
        spineMat,    // -X left (spine)
        pageMat,     // +Y top (page edges)
        pageMat,     // -Y bottom (page edges)
        coverMat,    // +Z front (cover art)
        backCoverMat // -Z back (back cover)
      ];

      // Async load real cover image if available
      if (book.imageUrl) {
        (function (cMat, imgUrl) {
          textureLoader.load(
            imgUrl,
            function (tex) {
              tex.encoding = THREE.sRGBEncoding;
              cMat.map = tex;
              cMat.needsUpdate = true;
            },
            undefined,
            function () {
              // Keep procedural cover on error
            }
          );
        })(coverMat, book.imageUrl);
      }

      var bookGeo = new THREE.BoxGeometry(bookW, bookH, bookD);
      var bookMesh = new THREE.Mesh(bookGeo, mats);

      var posY = shelfY + (bookH / 2);
      var posZ = 0.1;

      // Slight natural variations
      var tiltZ = (i % 7 === 3) ? (0.04) : ((i % 7 === 5) ? -0.04 : 0);
      var angleY = 0.05 + (Math.sin(i * 1.5) * 0.04);

      bookMesh.position.set(curX + (bookW / 2), posY, posZ);
      bookMesh.rotation.set(0, angleY, tiltZ);
      bookMesh.castShadow = true;
      bookMesh.receiveShadow = true;

      // Custom metadata for interaction
      bookMesh.userData = {
        book: book,
        category: group.label,
        dataKey: group.dataKey,
        origPos: bookMesh.position.clone(),
        origRot: bookMesh.rotation.clone(),
        currentPosZ: posZ,
        targetPosZ: posZ,
        targetRotY: angleY,
        shelfY: posY
      };

      scene.add(bookMesh);
      bookMeshes.push(bookMesh);

      curX += bookW + 0.35;
    }
  }

  // --- Interaction & Raycasting ---
  function onMouseMove(event) {
    var rect = container.getBoundingClientRect();
    mouse.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
    mouse.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;
  }

  function onMouseLeave() {
    mouse.x = -9999;
    mouse.y = -9999;
    if (hoveredBook && hoveredBook !== selectedBook) {
      hoveredBook.userData.targetPosZ = hoveredBook.userData.origPos.z;
      hoveredBook = null;
      container.style.cursor = 'default';
    }
  }

  function onCanvasClick(event) {
    if (hoveredBook) {
      selectBook(hoveredBook);
    } else {
      deselectBook();
    }
  }

  function selectBook(mesh) {
    if (selectedBook && selectedBook !== mesh) {
      deselectBook();
    }

    selectedBook = mesh;
    selectedBook.userData.targetPosZ = selectedBook.userData.origPos.z + 1.8;
    selectedBook.userData.targetRotY = 0;

    // Focus camera slightly towards the selected book
    targetLookAt.x = mesh.position.x;
    targetLookAt.y = mesh.position.y;
    targetLookAt.z = 0;

    showBookModal(mesh.userData.book, mesh.userData.category);
  }

  function deselectBook() {
    if (selectedBook) {
      selectedBook.userData.targetPosZ = selectedBook.userData.origPos.z;
      selectedBook.userData.targetRotY = selectedBook.userData.origRot.y;
      selectedBook = null;
    }
    hideBookModal();
    targetLookAt.x = defaultTarget.x;
    targetLookAt.y = defaultTarget.y;
    targetLookAt.z = defaultTarget.z;
  }

  // --- Modal Management ---
  function showBookModal(book, category) {
    if (!modal) return;
    if (modalCategory) modalCategory.textContent = category || 'Book';
    if (modalTitle) modalTitle.textContent = book.title || 'Untitled';
    if (modalAuthor) modalAuthor.textContent = book.author ? 'by ' + book.author : '';
    if (modalDesc) modalDesc.textContent = book.description || 'No summary available for this book.';

    if (modalRating) {
      var r = parseInt(book.rating || '0', 10);
      if (r > 0) {
        modalRating.innerHTML = '<span class="stars">' + '★'.repeat(r) + '☆'.repeat(5 - r) + '</span> ' + r + '/5';
      } else {
        modalRating.innerHTML = '';
      }
    }

    if (modalCover) {
      if (book.imageUrl) {
        modalCover.innerHTML = '<img src="' + book.imageUrl + '" alt="' + (book.title || 'Cover') + '">';
      } else {
        var pal = getPaletteForBook(book.title || '');
        modalCover.innerHTML = '<div class="book-placeholder" style="background:' + pal.bg + ';color:' + pal.fg + '">' + (book.title || '') + '</div>';
      }
    }

    if (modalLink) {
      if (book.link && book.link !== '#') {
        modalLink.href = book.link;
        modalLink.style.display = 'inline-block';
      } else {
        modalLink.style.display = 'none';
      }
    }

    modal.classList.remove('hidden');
    modal.setAttribute('aria-hidden', 'false');
  }

  function hideBookModal() {
    if (!modal) return;
    modal.classList.add('hidden');
    modal.setAttribute('aria-hidden', 'true');
  }

  if (modalClose) {
    modalClose.addEventListener('click', function (e) {
      e.stopPropagation();
      deselectBook();
    });
  }

  if (modalBackdrop) {
    modalBackdrop.addEventListener('click', function (e) {
      e.stopPropagation();
      deselectBook();
    });
  }

  // --- Filtering & Search ---
  function applyFilters() {
    var query = searchQuery.trim().toLowerCase();

    // 3D Scene updates
    bookMeshes.forEach(function (mesh) {
      var b = mesh.userData.book;
      var matchesCat = (currentFilter === 'all' || mesh.userData.dataKey === currentFilter);
      var matchesSearch = !query ||
        (b.title && b.title.toLowerCase().indexOf(query) !== -1) ||
        (b.author && b.author.toLowerCase().indexOf(query) !== -1);

      var isVisible = matchesCat && matchesSearch;
      mesh.visible = isVisible;

      if (isVisible && query) {
        mesh.userData.targetPosZ = mesh.userData.origPos.z + 0.4;
      } else if (mesh !== selectedBook) {
        mesh.userData.targetPosZ = mesh.userData.origPos.z;
      }
    });

    // 2D View updates
    if (container2D) {
      var sections = container2D.querySelectorAll('.shelf-section');
      sections.forEach(function (sec) {
        var label = sec.querySelector('.shelf-label');
        var isCurated = label && label.classList.contains('tag-curated');
        var isCurrent = label && label.classList.contains('tag-current');
        var isRead = label && label.classList.contains('tag-read');

        var secCategory = isCurated ? 'curated' : (isCurrent ? 'currently-reading' : 'read');
        var catMatch = (currentFilter === 'all' || secCategory === currentFilter);

        var cards = sec.querySelectorAll('.book');
        var visibleCount = 0;
        cards.forEach(function (card) {
          var titleEl = card.querySelector('.book-tooltip b');
          var authorEl = card.querySelector('.book-tooltip span');
          var title = titleEl ? titleEl.textContent.toLowerCase() : '';
          var author = authorEl ? authorEl.textContent.toLowerCase() : '';

          var cardMatch = !query || title.indexOf(query) !== -1 || author.indexOf(query) !== -1;
          if (catMatch && cardMatch) {
            card.style.display = 'block';
            visibleCount++;
          } else {
            card.style.display = 'none';
          }
        });

        sec.style.display = (catMatch && visibleCount > 0) ? 'block' : 'none';
      });
    }
  }

  filterChips.forEach(function (chip) {
    chip.addEventListener('click', function () {
      filterChips.forEach(function (c) { c.classList.remove('active'); });
      chip.classList.add('active');
      currentFilter = chip.getAttribute('data-filter') || 'all';
      applyFilters();
    });
  });

  if (searchInput) {
    searchInput.addEventListener('input', function (e) {
      searchQuery = e.target.value;
      applyFilters();
    });
  }

  if (resetCamBtn) {
    resetCamBtn.addEventListener('click', function () {
      deselectBook();
      targetCamPos.x = defaultCamPos.x;
      targetCamPos.y = defaultCamPos.y;
      targetCamPos.z = defaultCamPos.z;
      targetLookAt.x = defaultTarget.x;
      targetLookAt.y = defaultTarget.y;
      targetLookAt.z = defaultTarget.z;
    });
  }

  // --- Animation Loop ---
  function animate() {
    requestAnimationFrame(animate);

    // Raycast for hover
    raycaster.setFromCamera(mouse, camera);
    var visibleMeshes = bookMeshes.filter(function (m) { return m.visible; });
    var intersects = raycaster.intersectObjects(visibleMeshes);

    if (intersects.length > 0) {
      var hit = intersects[0].object;
      if (hoveredBook !== hit) {
        if (hoveredBook && hoveredBook !== selectedBook) {
          hoveredBook.userData.targetPosZ = hoveredBook.userData.origPos.z;
        }
        hoveredBook = hit;
        if (hoveredBook !== selectedBook) {
          hoveredBook.userData.targetPosZ = hoveredBook.userData.origPos.z + 0.45;
        }
        container.style.cursor = 'pointer';
      }
    } else {
      if (hoveredBook && hoveredBook !== selectedBook) {
        hoveredBook.userData.targetPosZ = hoveredBook.userData.origPos.z;
        hoveredBook = null;
      }
      container.style.cursor = 'default';
    }

    // Smooth Lerp for book hover / click animations
    for (var i = 0; i < bookMeshes.length; i++) {
      var m = bookMeshes[i];
      m.position.z += (m.userData.targetPosZ - m.position.z) * 0.12;
      m.rotation.y += (m.userData.targetRotY - m.rotation.y) * 0.12;
    }

    // Smooth camera target lerp
    if (controls) {
      controls.target.x += (targetLookAt.x - controls.target.x) * 0.05;
      controls.target.y += (targetLookAt.y - controls.target.y) * 0.05;
      controls.target.z += (targetLookAt.z - controls.target.z) * 0.05;
      controls.update();
    }

    renderer.render(scene, camera);
  }

  function onWindowResize() {
    if (!renderer || !camera || !container) return;
    var width = container.clientWidth || 900;
    var height = 580;
    camera.aspect = width / height;
    camera.updateProjectionMatrix();
    renderer.setSize(width, height);
  }

  // Run on DOM ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initThree);
  } else {
    initThree();
  }
})();
