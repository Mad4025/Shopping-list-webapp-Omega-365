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
    .then(data => updateCartModal(data.cart))
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

function enableEditing(itemId, itemName, category, quantity) {
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
    const itemName = ' ' + document.getElementById(`edit-item-name-${itemId}`).value;
    const category = ' ' + document.getElementById(`edit-category-${itemId}`).value;
    const quantity = ' ' + document.getElementById(`edit-quantity-${itemId}`).value;

    fetch(`/edit-item/${itemId}`, {
        method: 'PUT',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ itemName, category, quantity })
    })
    .then(response => response.json())
    .then(data => {
        if(data.status === 'success') {
            // Update static display
            document.getElementById(`static-item-name-${itemId}`).textContent = itemName;
            document.getElementById(`static-category-${itemId}`).textContent = category;
            document.getElementById(`static-quantity-${itemId}`).textContent = quantity;
            cancelEditing(itemId)
        } 
        else {
            alert('Failed to update item.');
            cancelEditing(itemId)
        }
    })
    .catch(error => console.error('Error:', error));
}