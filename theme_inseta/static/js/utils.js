function validateEmail(email) {
    var ss = /@/i;
    var r = email.search(ss);
    if (r == -1) {
        return false;
    }
    return true;
}

// function validateFields(field){
//     if (field == ""){
//         alert("Please provide a valid field and proceed!!!");
//         return false;
//     }
//     return true;

// }
function validatePhone(phone) {

    if(phone ==undefined) return false;
    var stripped = phone.replace(/[\(\)\.\-\ ]/g, '');
    var illegalChars = /[\(\)\&lt;\&gt;\,\;\:\\\[\-\]]/;

    if (stripped == "") {
        alert("You didn't enter a valid phone number");
        return false;
    }
    if (phone.match(illegalChars)) {
        alert("The Cell/Phone/Fax number contains illegal characters");
        return false;
    } else if (isNaN(stripped)) {
        alert("The Cell/Phone/Fax number is not numbers only.");
        return false;
    } else if (!(stripped.length == 10)) {
        alert("The Cell/Phone/Fax number is the wrong length.");
        return false;
    }
    return true

}

// function validatePhone(phone) {
//     //remove empty spaces
//     _phone = phone.trim().replace(/\s/g, '')
//     var phoneRegex = /^\+[0-9]{1,3}\d{10}$/gm
//     if (phoneRegex.test(_phone)) {
//         return true;
//     }
//     return false;
// }
