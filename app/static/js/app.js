function addToOrder(productId) {
    const data = {
        product_id: productId,
        quantity: 1,
        sugar_level: "50%"
    };

    fetch('/order', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(data => alert(data.message || 'Order placed successfully!'))
    .catch(error => console.error('Error:', error));
}
let orders = [];
let subtotal = 0;
const taxRate = 0.1;

function addToOrder(id, name, price) {
    const existingOrder = orders.find(order => order.id === id);

    if (existingOrder) {
        existingOrder.quantity++;
    } else {
        orders.push({ id, name, price, quantity: 1 });
    }

    updateOrderList();
}

function updateOrderList() {
    const orderList = document.getElementById('order-list');
    orderList.innerHTML = '';
    subtotal = 0;

    orders.forEach(order => {
        const orderItem = document.createElement('div');
        orderItem.className = 'order-item';
        orderItem.innerHTML = `
            <span>${order.name} x${order.quantity}</span>
            <span>$${(order.price * order.quantity).toFixed(2)}</span>
        `;
        orderList.appendChild(orderItem);
        subtotal += order.price * order.quantity;
    });

    document.getElementById('subtotal').innerText = `$${subtotal.toFixed(2)}`;
    const tax = subtotal * taxRate;
    document.getElementById('tax').innerText = `$${tax.toFixed(2)}`;
    document.getElementById('total').innerText = `$${(subtotal + tax).toFixed(2)}`;
}

function proceedOrder() {
    alert('Order placed successfully!');
    orders = [];
    updateOrderList();
}
