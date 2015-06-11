
self.onload = function() {
   addDaySeparators();
}

function addDaySeparators() {
    if (!document.getElementsByClassName) {
        // for IE
        document.getElementsByClassName = function(c) {
            return this.querySelectorAll("."+c);
        };
    }
    var now = (new Date()).getTime();
    var curDay = '';
    var seps = document.getElementsByClassName('daysep');
    seps = Array.prototype.slice.call(seps, 0);
    for (var i=0; i<seps.length; i++) {
        var msdiff = seps[i].innerHTML * 1000;
        var day = new Date(now - msdiff).prettify();
        if (day != curDay) {
            seps[i].innerHTML = day;
            seps[i].setAttribute('class', 'daysepActive');
            curDay = day;
        }
    }
}

Date.prototype.prettify = function(abs) {
    var day = this.getDate();
    var mon = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'][this.getMonth()];
    var year = this.getFullYear();
    var absDate = (day > 9 ? day : '0'+day)+' '+mon+' '+year;
    if (abs) return absDate;
    var date = new Date();
    var today = date.prettify(true);
    if (absDate == today) return 'Today';
    var thisYear = date.getFullYear();
    date.setDate(date.getDate() - 1);
    var yesterday = date.prettify(true);
    if (absDate == yesterday) return 'Yesterday';
    if (this.getFullYear() == thisYear) return absDate.substr(0,absDate.length-4);
    return absDate;
}

function selectArea(t) {
    if (t == 'all') self.location.href=rootdir;
    else self.location.href=rootdir+t;
}

function edit(doc_id) {
    window.processing = false;
    var authors = document.getElementById('authors'+doc_id).innerHTML.replace(/'/g,'&#39;');
    var title = document.getElementById('title'+doc_id).innerHTML.replace(/'/g,'&#39;');
    var url = document.getElementById('title'+doc_id).getAttribute('href').replace(/'/g,'&#39;');
    var abstract = document.getElementById('abstract'+doc_id).innerHTML.replace(/'/g,'&#39;');
    self.dialog = document.createElement('div');
    dialog.setAttribute('id', 'editDialog');
    dialog.innerHTML = ["<h4>Edit entry ",
                        "<span id='closeBtn' onclick='document.body.removeChild(self.dialog)'>X</div></h4>",
                        "<form method='post' action="+rootdir+"_editdoc' id='editform' onsubmit='return submit_edit()'>",
                        "<input type='hidden' name='doc_id' value='"+doc_id+"'>",
                        "<input type='hidden' name='doc_url' value='"+url+"'>",
                        "<input type='hidden' name='oppdocs' value='"+oppdocs+"'>",
                        "<input type='hidden' name='next' value='"+self.location.href+"'>",
                        "<label for='authors'>Authors:</label><br>",
                        "<input type='text' name='authors' value='"+authors+"'><br>",
                        "<label for='title'>Title:</label><br>",
                        "<input type='text' name='title' value='"+title+"'><br>",
                        "<label for='abstract'>Abstract:</label><br>",
                        "<textarea name='abstract'>"+abstract+"</textarea><br>",
                        "<input type='submit' name='submit' value='Submit Changes'>",
                        "<input type='submit' name='submit' value='Discard Entry' onclick='submit_edit(1)'>",
                        "</form>"].join("");
    document.body.appendChild(dialog);
}

function submit_edit(discard) {
    // submitting the form by AJAX to get around problems with the dual-server setup 
    if (window.processing) return false;
    window.processing = true;
    var f = document.forms['editform'];
    var doc_id = f.elements['doc_id'].value;
    var oppdocs = f.elements['oppdocs'].value;
    var doc_url = encodeURIComponent(f.elements['doc_url'].value);
    var authors = encodeURIComponent(f.elements['authors'].value);
    var title = encodeURIComponent(f.elements['title'].value);
    var abstract = encodeURIComponent(f.elements['abstract'].value);
    var submit = discard ? 'Discard Entry' : 'Submit Changes';
    var req = new XMLHttpRequest();
    var url = rootdir+"_editdoc";
    var params = 'doc_id='+doc_id+'&doc_url='+doc_url+'&oppdocs='+oppdocs;
    params += '&authors='+authors+'&title='+title+'&abstract='+abstract;
    params += '&submit='+submit+'&next='+self.location.href;
    req.open('POST', url, true);
    req.setRequestHeader("Content-type", "application/x-www-form-urlencoded");
    req.setRequestHeader("Content-length", params.length);
    req.setRequestHeader("Connection", "close");
    req.onreadystatechange = function() {
        if (req.readyState == 4) {
            if (req.status == 200) self.location.reload();
            else alert(req.responseText);
        }
    }
    req.send(params);
    document.body.removeChild(self.dialog);
    return false;
}
