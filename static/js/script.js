// Ensure DOM (Document Object Model) is fully loaded before calling filterDropdown.
document.addEventListener('DOMContentLoaded', () => {
    const filterDropdown = document.getElementById('categoryFilter');
    const itemList = document.getElementById('itemList');
    
    if (!filterDropdown || !itemList) {
        console.error('Filter dropdown or item list not found');
        return;
    }

    filterDropdown.addEventListener('change', function() {
        const selectedCategory = this.value;
        const items = itemList.querySelectorAll('.col-custom-5');
        
        console.log('Selected category:', selectedCategory); // Debug
        console.log('Found items:', items.length); // Debug
        
        items.forEach(item => {
            const itemCategory = item.getAttribute('data-category');
            console.log('Item category:', itemCategory); // Debug
            
            if (selectedCategory === 'all' || itemCategory === selectedCategory) {
                item.classList.remove('d-none');
            } else {
                item.classList.add('d-none');
            }
        });
    });
});

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

// Fetch cart contents when clicking 'view cart'
document.getElementById('viewCartBtn').addEventListener('click', () => {
    fetch('/get-cart', {method:'GET'})
    .then(response => response.json())
    .then(data => updateCartModal(data.cart))
    .catch(error => console.error('Error:', error))

    const cartModal = new bootstrap.Modal(document.getElementById('cartModal'));
    cartModal.show();
});

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