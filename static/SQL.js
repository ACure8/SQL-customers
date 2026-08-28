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