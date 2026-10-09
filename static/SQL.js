// SIGN UP tab will be viewed so adding these elements will start animations
function showSignup() {
  document.body.classList.add('interactive');
  var login = document.getElementById('loginForm');
  var signup = document.getElementById('signupForm');
  var forgot = document.getElementById('forgotForm');
  var tabsignin = document.getElementById('signin');
  var tabsignup = document.getElementById('signup');

  if (login) login.classList.remove('active'); tabsignin.classList.remove('active');
  if (signup) signup.classList.add('active'); tabsignup.classList.add('active');
  if (forgot) forgot.classList.remove('active');
}

// SIGN IN tab will be viewed so adding these elements will start animations
function showSignin() {
  document.body.classList.add('interactive');
  var login = document.getElementById('loginForm');
  var signup = document.getElementById('signupForm');
  var forgot = document.getElementById('forgotForm');
  var tabsignin = document.getElementById('signin');
  var tabsignup = document.getElementById('signup');

  if (login) login.classList.add('active'); tabsignin.classList.add('active');
  if (signup) signup.classList.remove('active'); tabsignup.classList.remove('active');
  if (forgot) forgot.classList.remove('active');
}

// FORGOT PASSWORD will be shown, and hides the other tabs
function showForgotPassword() {
  document.body.classList.add('interactive');
  var login = document.getElementById('loginForm');
  var signup = document.getElementById('signupForm');
  var forgot = document.getElementById('forgotForm');
  var tabsignin = document.getElementById('signin');
  var tabsignup = document.getElementById('signup');

  if (login) login.classList.remove('active'); tabsignin.classList.remove('active');
  if (signup) signup.classList.remove('active'); tabsignup.classList.remove('active');
  if (forgot) forgot.classList.add('active');
}

// Client-sided validation for the signup form before it reaches the server.
// This gives quick feedback if passwords do not match or too short.
document.addEventListener('submit', function (e) {
  if (e.target && e.target.id === 'signupFormSubmit') {
    var pwd = e.target.querySelector('input[name="password"]');
    var conf = e.target.querySelector('input[name="confirm_password"]');
    if (pwd && conf && pwd.value !== conf.value) {
      e.preventDefault();
      alert('Passwords do not match');
    }
    if (pwd && pwd.value.trim().length < 8) {
      e.preventDefault();
      alert('Passwords must be at least 8 characters long!');
    }
  }
});


// This handles category selection on the menu page.
// The selected category is highlighted and only matching products are shown.
function movecategories(clickedEl) {
  const selectedCategoryId = clickedEl.dataset.categoryId;

  document.querySelectorAll('.categorycard').forEach(cc => {
    cc.classList.add('move');
    cc.classList.toggle('selected', cc === clickedEl);
  });
  document.querySelectorAll('.productcards').forEach(product => {
    product.hidden = product.dataset.categoryId !== selectedCategoryId;
  });
  var categorylist = document.getElementById('categorylist');

  if (categorylist) {
    categorylist.classList.add('move');
    requestAnimationFrame(() => {
      var targetLeft = clickedEl.offsetLeft - (categorylist.clientWidth - clickedEl.offsetWidth) / 2;
      categorylist.scrollTo({ left: Math.max(0, targetLeft), behavior: 'smooth' });
    });
  }
}

// Duplicate the carousel slides so the slide show can loop endlessly.
(() => {
  const track = document.querySelector('.carousel__track');
  if (!track) return;

  Array.from(track.children).forEach(slide => {
    const clone = slide.cloneNode(true);
    clone.setAttribute('aria-hidden', 'true');
    track.append(clone);
  });
})();

// Initialize cart interactions when the cart page loads.(how the page handles information that it's given)
function startCartPage() {
  const summary = document.querySelector('.cart-summary');
  const cartError = document.querySelector('.cart-error');
  const deliveryFee = Number(summary?.dataset.deliveryFee || 0);
  const taxRate = Number(summary?.dataset.taxRate || 0);

  // Keeps the quantity options in sync with stock limits and disabled(unavailable) states.
  const syncQuantityControls = (item) => {
    const input = item.querySelector('.qty-input');
    const decreaseButton = item.querySelector('[data-action="decrease"]');
    const increaseButton = item.querySelector('[data-action="increase"]');
    if (!input || !decreaseButton || !increaseButton) return;

    const quantity = Number(input.value || 1);
    const stockLimit = Number(item.dataset.stock || 0);
    if (!item.dataset.previousQuantity) item.dataset.previousQuantity = input.value;
    input.min = '1';
    input.max = String(Math.max(1, stockLimit));
    decreaseButton.disabled = quantity <= 1;
    increaseButton.disabled = quantity >= stockLimit;
  };

  // Live recalculation of subtotal, tax, delivery, and total after any quantity change.
  const updateCartTotal = () => {
    const items = document.querySelectorAll('.cart-item');
    let total = 0;

    items.forEach((item) => {
      const price = Number(item.dataset.price || 0);
      const quantity = Number(item.querySelector('.qty-input')?.value || 0);
      const lineTotal = price * quantity;
      total += lineTotal;

      const totalEl = item.querySelector('.item-total');
      if (totalEl) totalEl.textContent = `$${lineTotal.toFixed(2)}`;
      syncQuantityControls(item);
    });

    const subtotal = Math.round((total + Number.EPSILON) * 100) / 100;
    const tax = Math.round((subtotal * taxRate + Number.EPSILON) * 100) / 100;
    const delivery = subtotal > 0 ? deliveryFee : 0;
    const subtotalEl = document.querySelector('.cart-subtotal');
    const deliveryEl = document.querySelector('.delivery-total');
    const taxEl = document.querySelector('.tax-total');
    const orderTotalEl = document.querySelector('.order-total');

    if (subtotalEl) subtotalEl.textContent = `$${subtotal.toFixed(2)}`;
    if (deliveryEl) deliveryEl.textContent = `$${delivery.toFixed(2)}`;
    if (taxEl) taxEl.textContent = `$${tax.toFixed(2)}`;
    if (orderTotalEl) orderTotalEl.textContent = `$${(subtotal + delivery + tax).toFixed(2)}`;
  };

  // Send the updated cart quantity to the server without reloading the page.
  const sendQuantityUpdate = async (productId, quantity) => {
    const formData = new URLSearchParams({
      product_id: productId,
      action: 'update',
      quantity: String(quantity)
    });

    const response = await fetch('/cart', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'X-Requested-With': 'XMLHttpRequest'
      },
      body: formData.toString()
    });
    const result = await response.json();
    if (!response.ok || result?.status !== 'ok') {
      throw new Error(result?.message || 'Failed to update cart');
    }
    return result;
  };

  // Displays a cart error message if the server rejects the update.
  const showCartError = (error) => {
    if (!cartError) return;
    cartError.textContent = error.message;
    cartError.hidden = false;
  };

  // Handles the +/- quantity buttons for each cart item.
  document.querySelectorAll('.qty-btn').forEach((button) => {
    button.addEventListener('click', async () => {
      const stepper = button.closest('.qty-stepper');
      const input = stepper?.querySelector('.qty-input');
      const item = button.closest('.cart-item');
      if (!stepper || !input || !item) return;

      const productId = item.dataset.productId;
      const currentValue = Number(input.value || 1);
      const stockLimit = Number(item.dataset.stock || 0);
      if (button.dataset.action === 'decrease' && currentValue <= 1) return;
      if (button.dataset.action === 'increase' && currentValue >= stockLimit) return;

      const nextValue = button.dataset.action === 'increase' ? currentValue + 1 : currentValue - 1;
      input.value = nextValue;
      try {
        await sendQuantityUpdate(productId, nextValue);
        item.dataset.previousQuantity = String(nextValue);
        if (cartError) cartError.hidden = true;
        updateCartTotal();
      } catch (error) {
        input.value = currentValue;
        syncQuantityControls(item);
        showCartError(error);
      }
    });
  });

  // If a user types a quantity manually, we want to make sure if that is fine and if not we'll need to reduce it and save it.
  document.querySelectorAll('.qty-input').forEach((input) => {
    input.addEventListener('change', async () => {
      const item = input.closest('.cart-item');
      if (!item) return;

      const productId = item.dataset.productId;
      const previousValue = Number(item.dataset.previousQuantity || input.defaultValue || 1);
      const stockLimit = Number(item.dataset.stock || 0);
      const requestedValue = Number(input.value || 1);
      const nextValue = Math.min(
        Math.max(1, stockLimit),
        Math.max(1, Math.floor(Number.isFinite(requestedValue) ? requestedValue : 1))
      );
      input.value = nextValue;

      try {
        await sendQuantityUpdate(productId, nextValue);
        item.dataset.previousQuantity = String(nextValue);
        if (cartError) cartError.hidden = true;
        updateCartTotal();
      } catch (error) {
        input.value = previousValue;
        syncQuantityControls(item);
        showCartError(error);
      }
    });
  });

  // Prevent duplicate remove clicks while the item is being deleted.
  document.querySelectorAll('.remove-form').forEach((form) => {
    form.addEventListener('submit', () => {
      const submitButton = form.querySelector('button[type="submit"]');
      if (submitButton) submitButton.disabled = true;
    });
  });

  updateCartTotal();
}

document.addEventListener('DOMContentLoaded', () => {
  if (document.querySelector('.cart-item')) {
    startCartPage();
  }
});