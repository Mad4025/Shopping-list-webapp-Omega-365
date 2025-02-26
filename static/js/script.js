function addToCart(itemName) {
    fetch('/add-to-cart', {
        method: 'POST',
        headers: {'Content-Type': 'application/x-www-form-urlencoded'},
        body: `item_name=${encodeURIComponent(itemName)}`
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            updateCartModal(data.cart);

            const stockElement = document.getElementById(`static-quantity-${data.item_id}`)
            if (stockElement) {
                stockElement.textContent = ` ${data.stock}`;

                // Disable button if stock is zero or less.
                if (data.stock <= 0) {
                    const addButton = stockElement.closest(`#static-${data.item_id}`).querySelector('.disable-if-not-enough');
                    if (addButton) addButton.disabled = true;
                }
            }

             // Display that you've added an item to the cart with Toast!
            var toastEl = document.getElementById('cartToast');
            var toast = new bootstrap.Toast(toastEl);
            toast.show();
        } 
        else {
            alert(data.message || 'Could not add item to cart.');
        }
    })
    .catch(error => console.error('Error:', error));
}

function deleteFromCart(itemId) {
    fetch('/delete-from-cart', {
        method: 'POST',
        headers: {'Content-Type': 'application/x-www-form-urlencoded'},
        body: `item_id=${itemId}`
    })
    .then(response => response.json())
    .then(data => {
        updateCartModal(data.cart)

        const stockElement = document.getElementById(`static-quantity-${data.item_id}`)
            if (stockElement) {
                stockElement.textContent = ` ${data.stock}`;
            }
    })
    .catch(error => console.error('Error:', error));
}

function updateCartModal(cart) {
    const cartList = document.getElementById('cartItemsList');
    cartList.innerHTML = '';
    cart.forEach(item => {
        const li = document.createElement('li');
        li.className = 'list-group-item d-flex justify-content-between align-items-center';
        li.innerHTML = `${item.item_name || 'Unknown Item'} (x${item.quantity}) 
        <button class="btn btn-danger btn-sm" onclick="deleteFromCart(${item.id})">Delete</button>`;
        cartList.appendChild(li);
    });
}

function enableEditing(itemId) {
    // Hide static display
    document.getElementById(`static-${itemId}`).style.display = 'none';
    // Show editable fields
    document.getElementById(`edit-${itemId}`).style.display = 'block';
}

function cancelEditing(itemId) {
    // Hide editable fields
    document.getElementById(`edit-${itemId}`).style.display = 'none';
    // Show static display
    document.getElementById(`static-${itemId}`).style.display = 'block'
}

function submitEditForm(itemId) {
    const itemName = document.getElementById(`edit-item-name-${itemId}`).value;
    const price = document.getElementById(`edit-price-${itemId}`).value;
    const quantity = document.getElementById(`edit-quantity-${itemId}`).value;
    const category = document.getElementById(`edit-category-${itemId}`).value;

    fetch(`/edit-item/${itemId}`, {
        method: 'PUT',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ itemName, price, quantity, category })
    })
    .then(response => response.json())
    .then(data => {
        if(data.status === 'success') {
            // Update static display
            document.getElementById(`static-item-name-${itemId}`).textContent = itemName;
            document.getElementById(`static-price-${itemId}`).textContent = price;
            document.getElementById(`static-quantity-${itemId}`).textContent = quantity;
            document.getElementById(`static-category-${itemId}`).textContent = category;
            cancelEditing(itemId)
        } 
        else {
            alert('Failed to update item.');
            cancelEditing(itemId)
        }
    })
    .catch(error => console.error('Error:', error));
}