
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
    var mon = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'][this.getMonth()];
    var year = this.getFullYear();
    var absDate = day+' '+mon+' '+year;
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


function updateDocList() {
    var typeSelect = document.forms['filterform'].elements['type'];
    var type = typeSelect.options[typeSelect.selectedIndex].value;
    var areaSelect = document.forms['filterform'].elements['area'];
    var area = areaSelect.options[areaSelect.selectedIndex].value;
    var url = rootdir;
    if (area != 'all') url += 't/'+area;
    if (type != 'all') url += '?type='+type;
    self.location.href = url;
}

function vote(doc_id, topic_id, class_id) {
    var req = new XMLHttpRequest();
    var url = rootdir+"train";
    var params = 'doc='+doc_id+'&topic_id='+topic_id+'&class='+class_id;
    req.open('GET', url+'?'+params, true);
    req.send();
    return false;
}

function popup(url, width, height) {
    width = width || 800;
    height = height || 600;
    window.open(url, 'opp', 'width='+width+',height='+height);
    return false;
}


function edit(doc_id) {
    var authors = document.getElementById('authors'+doc_id).innerHTML.replace(/'/g,'&#39;');
    var title = document.getElementById('title'+doc_id).innerHTML.replace(/'/g,'&#39;');
    var url = document.getElementById('title'+doc_id).getAttribute('href').replace(/'/g,'&#39;');
    var abs = document.getElementById('abstract'+doc_id).innerHTML.replace(/'/g,'&#39;');
    $('#id_authors').val(authors);
    $('#id_title').val(title);
    $('#id_abstract').val(abs);
    $('#id_doc_id').val(doc_id);
}

$(document).ready(function() {
    form = $('#editform');
    if (form) form.submit(function(e) {
        submit_edit();
        e.preventDefault();
    });
});

function submit_edit(discard) {
    var formData = {
        'csrfmiddlewaretoken': $('input[name=csrfmiddlewaretoken]').val(),
        'doc_id': $('input[name=doc_id]').val(),
        'authors': $('input[name=authors]').val(),
        'title': $('input[name=title]').val(),
        'abstract': $('#id_abstract').val(),
        'hidden': discard ? true : false,
    };
    $.ajax({
        type: 'POST',
        url: '/edit-doc',
        data: formData,
        dataType: 'json',
        encode: true
    }).done(function(data) {
        console.log(data); 
    });
}
