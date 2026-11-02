document.addEventListener('DOMContentLoaded', () => {
  const addRowButton = document.getElementById('add-row');
  const itemsContainer = document.getElementById('items-container');

  if (addRowButton && itemsContainer) {
    addRowButton.addEventListener('click', () => {
      const row = document.createElement('div');
      row.className = 'invoice-row';
      row.innerHTML = `
        <select name="product_id">
          <option value="">Select product</option>
          ${Array.from(document.querySelectorAll('select[name="product_id"] option')).slice(1).map(option => {
            return `<option value="${option.value}">${option.text}</option>`;
          }).join('')}
        </select>
        <input type="number" name="quantity" min="1" step="0.01" placeholder="Qty" />
      `;
      itemsContainer.appendChild(row);
    });
  }
});
