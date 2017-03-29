/*!
    Copyright (C) 2017 Google Inc.
    Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
*/

/* =========================================================
 * Extra scripts for beta designs
 * ========================================================= */

jQuery(function ($) {

  //render out templates function
  var renderExternalTmpl = function(item) {
    var file = '/design/templates/' + item.name;
    if ($(item.selector).length > 0) {
      $.when($.get(file)).done(function(tmplData) {
        $(item.selector).append(tmplData)
        //$.templates({ tmpl: tmplData });
        //$(item.selector).append($.render.tmpl(item.data));
      });
    }
  }


  renderExternalTmpl({ name: 'selectorSectionToControl', selector: '#templates', data: {} });
  renderExternalTmpl({ name: 'selectorSectionToControlNA', selector: '#templates', data: {} });



  $(document).on("click", "#expand_all", function(event) {
    //$('.row-fluid-slotcontent').show("fast");
    $('.row-fluid-slotcontent').addClass("in");
    $('.expander').addClass("toggleExpanded");
  });

  $(document).on("click", "#shrink_all", function(event) {
    //$('.row-fluid-slotcontent').hide("fast");
    $('.row-fluid-slotcontent').removeClass("in");
    $('.expander').removeClass("toggleExpanded");
  });

  /*Checkbutton in modals widget function*/
  $(document).on("click", ".checkbutton", function(event) {
    $(this).children("i").toggleClass("fa-times");
  });

  /*Toggle widget function*/
  $(document).on("click", ".accordion-toggle", function(event) {
    $(this).children("i").toggleClass("fa fa-caret-right");
  });

  /*Toggle slot function*/
  // Handled by rotation of expander icon
  /*$(document).on("click", ".toggle", function(event){
    $(this).children(".expander").toggleClass("toggleExpanded");
  });*/

  $(document).on("click", ".expandAll", function(event) {
    // $("h3.trigger").toggleClass("active").next().slideToggle("fast");
    $(this).children("i").toggleClass("fa fa-caret-right");
  });

  //Handle remove buttons
  $(document).on("click", ".removeCircleButton", function(event){
    //alert("here");
    $('#confirmModal').on('hidden', function () {
      $(this).closest('.controlSlot').remove();
    })
    $('#confirmModal').modal('show');
  });

/* no worky
  $(document).on("click", ".sluggroup", function(event){
    //alert("here");
    var $this = $(this);
    $('.sluggroup').removeClass('selected');
    $this.addClass('selected');
  });
*/

  $(document).on("click", ".greyOut", function(event){
    $(this).closest('.singlecontrolSlot').remove();
  });

  $(".addpersonItem").click(function () {
    $('#modalpeopleList').append("<li class='controlSlot ui-draggable'><div class='arrowcontrols-group'> <div class='controls-type'>Controls-Type</div><div class='controls-subtype'> <a class='dropdown-toggle statustextred' data-toggle='dropdown' href='#'>Select Role</a> <ul class='dropdown-menu dropdown-menusmall'><li>Admin</li><li>User</li></ul> </div>  <div class='controls-subgroup'>Controls-Subgroup</div></div><a class='personItem'><div class='removeCircleButton fltrt'><i class='gcmssmallicon-dash-white'></i></div></a></li>");
  });

  $(".referenceItem").click(function () {
    $('#referenceList').append("<li class='controlSlot'><a href='#'><div class='circle fltrt'><i class='gcmssmallicon-dash-white'></i></div></a><span class='controls-group'>Reference Type</span><br /><span class='controls-subgroup'>Reference Item</span></li>");
  });

  $('#quicklinks a:last').tab('show');

  $('#myLock a').click(function (e) {
      e.preventDefault();
      $('#programinformationLocked').tab('hide');
      $('#programinformationUnlocked').tab('show');
  });

//if includes a xpander we need to toggle it.
$('body').on('click', '.fa fa-caret-right', function(e) {
  //bootstrap data toggle opens this one up, but ...

  e.preventDefault();

  //var title = $("em").attr("data-target");

  var $this = $(this),
    slotcontent = $this.closest(".slot").find(".slottitle").attr("data-target"),
    $thisexpander = $this.closest(".slot").find(".expander");

    if (! $thisexpander.hasClass('in')) {

      $thisexpander.addClass('in');
      $(slotcontent).collapse('show');
    } else if ($thisexpander) {
      //$thisexpander.removeClass('in');
      //$(slotcontent).collapse('hide');

    }



  $("[id$=-more]").each(function(i){
      var el = $(this);
      if (el.hasClass("in")) {
        //its open close it!
        el.collapse('hide');
      } else {
        //its already closed, relax.
        // We have an isue with items on their way to closing and you clicked another, so checking for animating...
        el.filter(":animated").toggleClass("in");
      }
  });
});

  // show/hide widget

  $('body').on('click', '.widget-trigger', function(e) {
    e.preventDefault();
    var $this = $(this),
        $widgetBody = $this.closest(".widget").find(".widget-body"),
        $icon = $this.find("i");

    if( $this.hasClass("active") ) {
      $widgetBody.slideUp("fast");
      $this.removeClass("active");
      $icon
        .removeClass("icon-chevron-down")
        .addClass("icon-chevron-right");
    } else {
      $widgetBody.slideDown("fast");
      $this.addClass("active");
      $icon
        .removeClass("icon-chevron-right")
        .addClass("icon-chevron-down");
    }

  });

  // show/hide list item

  $('body').on('click', '.list-trigger', function(e) {
    e.preventDefault();
    var $this = $(this),
        $listBody = $this.closest(".wlist-title").next(),
        $icon = $this.find("i");

    if( $this.hasClass("active") ) {
      $listBody.slideUp("fast");
      $this.removeClass("active");
      $icon
        .removeClass("icon-chevron-down")
        .addClass("icon-chevron-right");
    } else {
      $listBody.slideDown("fast");
      $this.addClass("active");
      $icon
        .removeClass("icon-chevron-right")
        .addClass("icon-chevron-down");
    }

  });

  // nicer hover

  $('body').on('mouseenter', '.people-list li', function(e) {
    $(this).removeClass('.halfopacity');
    //$(this).find(".additional").slideDown("fast");
  });

  $('body').on('mouseleave', '.people-list li', function(e) {
    $(this).addClass('.halfopacity');
    //$(this).find(".additional").slideUp("fast");
  });

  $('body').on('click', '.people-list li', function(e) {

    if( $(this).find(".additional").hasClass("shown") ) {

    } else {
      //brute force ugly
       $(".additional").slideUp("shown");
       $(".additional").removeClass("shown");
       $(this).find(".additional").slideDown("fast");
       $(this).find(".additional").addClass("shown");
    }
  });


  // add item in target list

  $('body').on('click', '.add-me', function(e) {

    e.preventDefault();

    var $this = $(this),
        $icon = $this.find("i"),
        $itemToAdd = $this.closest("li"),
        $name = $itemToAdd.find(".name").html(),
        $company = $itemToAdd.find(".company").html(),
        $target = $this.closest(".modal-body").find(".target"),
        $unassignedItems = $("#unassignedElements"),
        $unassignedValue = parseInt($unassignedItems.html());

        var $additionalinfo = "";
    if ( $this.closest(".modal-body").find("#currentList").hasClass('category-list') ) {
      //Nothing
      //Pending approval, nothing in additional info
      var $item2add = '<h6 class="itemstatus">Added</h6>';
    } else if ($this.closest(".modal-body").find("#currentList").hasClass('people-list')) {
      //We gave relationships
      //Pending approval, start-stop
      var $item2add = '<div class="btn-group inline"> <a class="span7 btn btn-danger btn-mini dropdown-toggle nominheight fltrt" data-toggle="dropdown"> Select Relationship <span class="caret"></span> </a> <ul class="dropdown-menu"> <li> <a href="#" id="makeAccountable"> is Accountable for </a> </li> <li> <a href="#" id="makeResponsible"> is Responsible for </a> </li> </ul> </div>';
      var $additionalinfo = '<div class="row-fluid additional"> <div class="span4"></div> <div class="span4"> <label>Start Date (Optional)</label> <input class="span12 date" id="datepicker-stopdate-rd" placeholder="MM/DD/YYYY" type="text"> </div> <div class="span4"> <label>Stop Date (Optional)</label> <input class="span12 date" id="datepicker-stopdate-rd" placeholder="MM/DD/YYYY" type="text"> </div>';
    } else if ($this.closest(".modal-body").find("#currentList").hasClass('reference-list')) {
      //Will have assignment items, nothing now.
      //Pending approval, no start-stop
       var $item2add = '<h6 class="itemstatus">Added</h6>';
    } else if ($this.closest(".modal-body").find("#currentList").hasClass('system-list')) {
      //Will have assignment items, nothing now.
      //Pending approval, no start-stop
       var $item2add = '<h6 class="itemstatus">Added</h6>';
    }
    $this
      .removeClass("widgetbtn addme")
      .addClass("widgetbtnoff"); //remove icon square around checkmark (not a button anymore)
    $icon
      .removeClass("fa fa-caret-right")
      .addClass("fa fa-check-square-o green")
    $target
      .prepend('<li class="new-item"> <div class="row-fluid"> <div class="span6"> <span class="company">' + $company + '</span> <span class="name">'+ $name +'</span> </div> <div class="span6 actions">  <a class="widgetbtn pull-right" id="removeMe" href="#"> <i class="fa fa-ban"></i> </a> <a class="widgetbtn pull-right" href="#"> <i class="fa fa-pencil-square-o"></i> </a> ' + $item2add + '</div> </div>' + $additionalinfo +' </div> </li>')
      .find("li.new-item").hide().fadeIn('slow').removeClass("new-item");
    $unassignedItems
      .html($unassignedValue + 1).fadeIn();

    $(".itemstatus").effect("pulsate", { times:3 }, 800);
    $(".itemstatus").removeClass("itemstatus");
  });

  // show filters in modals

  $('body').on('click', '#makeAccountable', function(e) {
    e.preventDefault();
    $(this).closest(".btn-group").find(".dropdown-toggle").html("is Accountable");
    $(this).closest(".btn-group").find(".dropdown-toggle").removeClass('btn-warning');
    $(this).closest(".btn-group").find(".dropdown-toggle").addClass('btn-success');

    $(this).closest(".btn-group").find(".dropdown-toggle").addClass('halfopacity');
    $(this).closest(".btn-group").find(".dropdown-toggle").removeClass('btn-info');

  });

  $('body').on('click', '#makeResponsible', function(e) {
    e.preventDefault();
    $(this).closest(".btn-group").find(".dropdown-toggle").html("is Responsible");
    $(this).closest(".btn-group").find(".dropdown-toggle").removeClass('btn-warning');
    $(this).closest(".btn-group").find(".dropdown-toggle").addClass('btn-success');

    $(this).closest(".btn-group").find(".dropdown-toggle").addClass('halfopacity');
    $(this).closest(".btn-group").find(".dropdown-toggle").addClass('btn-info');

  });


  $(document).on("click", "#removeMe", function(event){
    event.preventDefault();
    $(this).closest('li').slideUp("slow", function() { jQuery(this).remove(); });
  });

  $('body').on('click', '#showFilters', function(e) {
    e.preventDefault();
    var $this = $(this),
        $filters = $this.closest(".modal-body").find(".filter-group"),
        $searchableLists = $this.closest(".modal-body").find(".filter-block .people-list");

    if( $this.hasClass("active") ) {
      $filters.hide();
      $this.removeClass("active");
      $searchableLists.removeClass("short");
    } else {
      $filters.show();
      $this.addClass("active");
      $searchableLists.addClass("short");
    }
  });

  $('body').on('click', '#showCategories', function(e) {
    e.preventDefault();
    var $this = $(this),
        $filters = $this.closest(".modal-body").find(".category-group"),
        $searchableLists = $this.closest(".modal-body").find(".filter-block .people-list");

    if( $this.hasClass("active") ) {
      $filters.hide();
      $this.removeClass("active");
      $searchableLists.removeClass("short");
    } else {
      $filters.show();
      $this.addClass("active");
      $searchableLists.addClass("short");
    }
  });


    $('body').on('click', '#showGRCDirectory', function(e) {
    e.preventDefault();
    var $this = $(this),
        $categoryfilters = $this.closest(".modal-body").find(".category-group"),
        $companyfilters = $this.closest(".modal-body").find(".filter-group"),
        $searchableLists = $this.closest(".modal-body").find(".filter-block .people-list");

      $categoryfilters.show();
      $companyfilters.hide();
      $this.addClass("active");
      $("#filterButton").html("GRC Directory <span class='caret'></span>");
      $searchableLists.removeClass("shortest");
      $searchableLists.addClass("short");
    //}
  });

$('body').on('click', '#showCompanyDirectory', function(e) {
    e.preventDefault();
    var $this = $(this),
        $categoryfilters = $this.closest(".modal-body").find(".category-group"),
        $companyfilters = $this.closest(".modal-body").find(".filter-group"),
        $searchableLists = $this.closest(".modal-body").find(".filter-block .people-list");

    //if( $this.hasClass("active") ) {
      //$filters.hide();
      //$this.removeClass("active");
      //$searchableLists.removeClass("short");
    //} else {
      $categoryfilters.hide();
      $companyfilters.show();
      $this.addClass("active");
      $("#filterButton").html("Company Directory <span class='caret'></span>");
      $searchableLists.addClass("shortest");
      $searchableLists.removeClass("short");
    //}
  });



  // status js
  var userHasPrivilege = true;
  $('body').on('click', '#actionButton', function(e) {
    e.preventDefault();

    var fullDate = new Date();
    var twoDigitMonth = ((fullDate.getMonth().length+1) === 1)? (fullDate.getMonth()+1) : '0' + (fullDate.getMonth()+1);
    var currentDate = fullDate.getDate() + "/" + twoDigitMonth + "/" + fullDate.getFullYear();

    var $this = $(this),
        $alert = $this.closest(".modal").find(".alert"),
        $date = $this.closest(".modal").find("#updatedDate"),
        $alertMessage = $this.closest(".modal").find("#alertMessage"),
        $status = $this.closest(".modal").find("#statusValue"),
        $currentStatus = $this.closest(".modal").find("#statusValue").html();

    if(userHasPrivilege) {

      if ($currentStatus === "Draft") {
        $status
          .html("Waiting for Approval")
          .addClass("statustextred");
        $alertMessage
          .html("New Program has been saved. Waiting on Approval.");
        $alert
          .fadeIn();
        $this
          .html("Approve");
        $date
          .html(currentDate);
      } else if ($currentStatus === "Waiting for Approval") {
        $status
          .html("Approved")
          .removeClass("statustextred");
        $alertMessage
          .html("Program has been approved.");
        $alert
          .fadeIn();
        $this
        .addClass("disabled");
        window.location = "/programs/1";
      }
    }
  });
});

function toggleGovernance() {
   var interval = 200;
  $('.govWidget').each(function(i){
    var el = $(this);
    if(el.hasClass('active')){
      $('#grcbutton-governance').addClass('halfopacity').removeClass('active');
      $.cookie('toggle_governance', null);
      el.delay(i*interval).slideUp(interval);
      el.removeClass('active');
    }else{
      $('#grcbutton-governance').removeClass('halfopacity').addClass('active');
      $.cookie('toggle_governance', '1', { expires: 1, path: '/' });
      el.delay(i*interval).slideDown(interval);
      el.addClass('active');
    }
  });

}

jQuery(function($) {
  if ($.cookie('toggle_governance') == '1')
    toggleGovernance();
  else
    $('.govWidget').hide();

  $('body').on('click', '#grcbutton-governance', function(e) {
    toggleGovernance();
    e.preventDefault();
  });
});

$(document).load(function(){
  $("#program_start_date").hide();
});
