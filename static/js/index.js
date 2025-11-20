document.addEventListener('DOMContentLoaded', () => {
  const search = document.getElementById('searchBox');
  const chips = document.querySelectorAll('.suggestions .chip');
  const form = document.querySelector('.search-form');
  const subjectLinks = document.querySelectorAll('.subject-link');
  const levelModal = document.getElementById('levelModal');
  const levelButtons = document.querySelectorAll('.level-btn');
  const levelClose = document.querySelector('.level-modal__close');
  let pendingMateria = null;

  chips.forEach(chip => {
    chip.addEventListener('click', () => {
      if (search) {
        search.value = chip.textContent.trim();
      }
      if (form) form.submit();
    });
  });

  if (search && form) {
    search.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') {
        e.preventDefault();
        form.submit();
      }
    });
  }

  const openModal = () => {
    if (levelModal) {
      levelModal.classList.add('show');
      levelModal.setAttribute('aria-hidden', 'false');
    }
  };

  const closeModal = () => {
    if (levelModal) {
      levelModal.classList.remove('show');
      levelModal.setAttribute('aria-hidden', 'true');
    }
  };

  if (subjectLinks.length && levelModal) {
    subjectLinks.forEach(link => {
      link.addEventListener('click', (event) => {
        event.preventDefault();
        pendingMateria = link.dataset.materia || link.textContent.trim();
        openModal();
      });
    });

    levelButtons.forEach(button => {
      button.addEventListener('click', () => {
        if (!pendingMateria) return;
        const level = button.dataset.level || 'facil';
        const baseUrl = '/test';
        const params = new URLSearchParams({ materia: pendingMateria, nivel: level });
        window.location.href = `${baseUrl}?${params.toString()}`;
      });
    });

    levelClose?.addEventListener('click', closeModal);
    levelModal.addEventListener('click', (event) => {
      if (event.target === levelModal) {
        closeModal();
      }
    });
  }

  const quizDataElement = document.getElementById('quizData');
  if (quizDataElement) {
    const questions = JSON.parse(quizDataElement.textContent || '[]');
    const total = questions.length;
    let currentIndex = 0;
    let score = 0;
    let answered = false;

    const questionTitle = document.getElementById('questionTitle');
    const optionsContainer = document.getElementById('optionsContainer');
    const feedbackBox = document.getElementById('feedbackBox');
    const feedbackResult = document.getElementById('feedbackResult');
    const feedbackTip = document.getElementById('feedbackTip');
    const progressLabel = document.getElementById('progressLabel');
    const progressFill = document.getElementById('progressFill');
    const nextButton = document.getElementById('nextButton');
    const questionLabel = document.getElementById('questionLabel');
    const summarySection = document.getElementById('quizSummary');
    const summaryText = summarySection?.querySelector('.summary-text');

    const renderQuestion = () => {
      answered = false;
      nextButton.disabled = true;
      nextButton.textContent = 'Siguiente pregunta';
      feedbackBox.classList.remove('show');
      const current = questions[currentIndex];
      if (!current) return;

      questionLabel.textContent = `Pregunta ${currentIndex + 1}`;
      questionTitle.textContent = current.question;
      progressLabel.textContent = `Pregunta ${currentIndex + 1} de ${total}`;
      progressFill.style.width = `${((currentIndex) / total) * 100}%`;

      optionsContainer.innerHTML = '';
      current.options.forEach(option => {
        const button = document.createElement('button');
        button.type = 'button';
        button.className = 'option-btn';
        button.textContent = option;

        button.addEventListener('click', () => {
          if (answered) return;
          answered = true;
          const isCorrect = option === current.correct;
          if (isCorrect) score += 1;

          Array.from(optionsContainer.children).forEach(btn => {
            const text = btn.textContent?.trim();
            btn.classList.remove('is-correct', 'is-incorrect');
            if (text === current.correct) {
              btn.classList.add('is-correct');
            } else if (text === option) {
              btn.classList.add('is-incorrect');
            }
          });

          feedbackBox.classList.add('show');
          feedbackResult.textContent = isCorrect ? '¡Correcto! 🎉' : 'Ups, no era esa 😺';
          feedbackTip.textContent = isCorrect ? '¡Seguí así!' : `Tip de GATTO: ${current.tip}`;

          nextButton.disabled = false;
          if (currentIndex + 1 >= total) {
            nextButton.textContent = 'Ver resultados';
          }
        });

        optionsContainer.appendChild(button);
      });
    };

    nextButton?.addEventListener('click', () => {
      if (!answered) return;
      currentIndex += 1;
      progressFill.style.width = `${(currentIndex / total) * 100}%`;

      if (currentIndex >= total) {
        summarySection?.classList.remove('hidden');
        summaryText.textContent = `Acertaste ${score} de ${total} preguntas.`;
        document.querySelector('.quiz-area').style.display = 'none';
      } else {
        renderQuestion();
      }
    });

    renderQuestion();
  }

  const alphabetToggle = document.querySelector('.alphabet-toggle');
  const alphabetPanel = document.getElementById('alphabetPanel');
  if (alphabetToggle && alphabetPanel) {
    alphabetToggle.addEventListener('click', () => {
      const isExpanded = alphabetToggle.getAttribute('aria-expanded') === 'true';
      alphabetToggle.setAttribute('aria-expanded', String(!isExpanded));
      alphabetPanel.classList.toggle('is-collapsed', isExpanded);
    });
  }
});



