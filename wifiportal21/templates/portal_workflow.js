
var timer;

window.onload = function() {
  poke_gateway();
  var message = document.getElementById('message');
  var spinner = document.getElementById('spinner');
  message.innerHTML = "<p>Logging on to WiFi gateway...</p>";
  message.style.display = '';
  spinner.style.display = '';
  timer = setInterval(registration_status, 5000);
};

function poke_gateway() {
  // Calling the captive portal gateway
  var request = new XMLHttpRequest();
  request.open('GET', '{{ auth_URL }}', true);
  request.send();
}

function registration_status() {
  // console.log("Checking registration status");
  var request = new XMLHttpRequest();
  var message = document.getElementById('message');
  var spinner = document.getElementById('spinner');
  var payment_request = document.getElementById('payment_request');

  request.open('GET', '/auth_status?token={{ token }}', true);
  request.onload = function() {
    if (request.status == 200) { // Status available
      var data = JSON.parse(request.responseText);
      if (data.status == "0") { // Logged in, need payment
        // console.log("Guest registration status LOGIN - requesting payment code");
        message.innerHTML = "<p>Getting payment address...</p>";
        message.style.display = '';
        spinner.style.display = '';
        get_payment_address();
        message.style.display = 'none';
        spinner.style.display = 'none';
      }
      else if (data.status == "1") { // Payment requested, Waiting
        // console.log("Guest registration status PAYREQ - checking payment");
        message.innerHTML = "<p>Waiting for your payment...</p>";
        message.style.display = '';
        spinner.style.display = '';
        get_payment_address();
        check_payment();
      }
      else if (data.status == "2") { // Paid - redirecting
        // console.log("Guest registration status PAID - redirecting to page");
        message.innerHTML = "<p>Payment received and access authorized. Redirecting...</p>";
        message.style.display = '';
        spinner.style.display = 'none';
        payment_request.style.display = 'none';
        // clear interval
        clearInterval(timer);
        // Redirect
        window.location = "{{ success_URL }}";
      }
    }
    else {
      // console.log("Guest registration status error - poking gateway");
      poke_gateway();
    }
  };
  request.send();
}

function get_payment_address() {
    var request = new XMLHttpRequest();
    request.open('GET', '/get_payment_address?token={{ token }}', true);
    request.onload = function() {
      if (request.status == 200) {
        var data = JSON.parse(request.responseText);
        var payment_request = document.getElementById('payment_request');
        payment_request.innerHTML = "<p>{{ price}}</p><div id=\"qr\"><img src=\"data:image/png;base64,"+ data.qr +"\"></div>" +
          "<br \><div id=\"address\">" + data.address + "</div>";
        payment_request.style.display = '';
      }
    };
    request.send();
}

function check_payment() {
  // console.log("Checking payment status");
  var request = new XMLHttpRequest();
  request.open('GET', '/check_payment?token={{ token }}', true);
  request.onload = function() {
    if (request.status == 200) { // Payment Received
      // console.log("Payment status: payment received");
    }
    else if (request.status == 402) {
      // console.log("Payment status: payment required");
    }
    else {
      // console.log("Payment status error" + request.status + request.responseText);
    }
  };
  request.send()
}
