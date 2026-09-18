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

// basic client-side signup confirm-password check
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


// function showSuccessMessage(message) {
//     // Create a temporary success notification
//     const notification = document.createElement('div');
//     notification.style.cssText = `
//         position: fixed;
//         top: 20px;
//         right: 20px;
//         background: #10b981;
//         color: white;
//         padding: 16px 24px;
//         border-radius: 12px;
//         font-weight: 600;
//         box-shadow: 0 10px 25px rgba(16, 185, 129, 0.3);
//         z-index: 1000;
//         animation: slideInRight 0.5s ease;
//     `;
//     notification.textContent = message;

//     document.body.appendChild(notification);

//     setTimeout(() => {
//         notification.remove();
function movecategories(clickedEl) {
  document.querySelectorAll('.categorycard').forEach(cc => {
    cc.classList.add('move');
    cc.classList.toggle('selected', cc === clickedEl);
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

(() => {
  const track = document.querySelector('.carousel__track');
  if (!track) return;

  Array.from(track.children).forEach(slide => {
    const clone = slide.cloneNode(true);
    clone.setAttribute('aria-hidden', 'true');
    track.append(clone);
  });
})();

function initializeCartPage() {
  const updateCartTotal = () => {
    const items = document.querySelectorAll('.cart-item');
    let total = 0;

    items.forEach((item) => {
      const price = Number(item.dataset.price || 0);
      const quantity = Number(item.querySelector('.qty-input')?.value || 0);
      const lineTotal = price * quantity;
      total += lineTotal;

      const totalEl = item.querySelector('.item-total');
      if (totalEl) {
        totalEl.textContent = `$${lineTotal.toFixed(2)}`;
      }
    });

    const totalEl = document.querySelector('.cart-total');
    if (totalEl) {
      totalEl.textContent = `$${total.toFixed(2)}`;
    }
  };

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

    if (!response.ok) {
      throw new Error('Failed to update cart');
    }

    return response.json();
  };

  const stepperButtons = document.querySelectorAll('.qty-btn');
  stepperButtons.forEach((button) => {
    button.addEventListener('click', async () => {
      const stepper = button.closest('.qty-stepper');
      const input = stepper?.querySelector('.qty-input');
      const item = button.closest('.cart-item');
      if (!stepper || !input || !item) return;

      const productId = item.dataset.productId;
      const currentValue = Number(input.value || 0);
      const nextValue = button.dataset.action === 'increase' ? currentValue + 1 : Math.max(0, currentValue - 1);
      input.value = nextValue;

      try {
        const result = await sendQuantityUpdate(productId, nextValue);
        if (result?.status === 'ok' && nextValue === 0) {
          item.remove();
        }
        updateCartTotal();
      } catch (error) {
        console.error(error);
        input.value = currentValue;
      }
    });
  });

  const inputs = document.querySelectorAll('.qty-input');
  inputs.forEach((input) => {
    input.addEventListener('change', async () => {
      const item = input.closest('.cart-item');
      if (!item) return;

      const productId = item.dataset.productId;
      const previousValue = Number(item.dataset.previousQuantity || input.value || 0);
      const nextValue = Math.max(0, Number(input.value || 0));
      input.value = nextValue;
      item.dataset.previousQuantity = String(nextValue);

      try {
        const result = await sendQuantityUpdate(productId, nextValue);
        if (result?.status === 'ok' && nextValue === 0) {
          item.remove();
        }
        updateCartTotal();
      } catch (error) {
        console.error(error);
        input.value = previousValue;
      }
    });
  });

  document.querySelectorAll('.remove-form').forEach((form) => {
    form.addEventListener('submit', (event) => {
      const item = form.closest('.cart-item');
      if (!item) return;
      const submitButton = form.querySelector('button[type="submit"]');
      if (submitButton) {
        submitButton.disabled = true;
      }
    });
  });

  updateCartTotal();
}

document.addEventListener('DOMContentLoaded', () => {
  if (document.querySelector('.cart-item')) {
    initializeCartPage();
  }
});