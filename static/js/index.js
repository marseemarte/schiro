document.addEventListener('DOMContentLoaded', () => {
  const search = document.getElementById('searchBox');
  const chips = document.querySelectorAll('.suggestions .chip');
  const form = document.querySelector('.search-form');

  chips.forEach(chip => {
    chip.addEventListener('click', () => {
      search.value = chip.textContent.trim();
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
});



