/*!
 Copyright (C) 2017 Google Inc.
 Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
 */

describe('can.mustache.helper.date', function () {
  'use strict';

  var helper;
  var testDate;

  beforeAll(function () {
    helper = can.Mustache._helpers.date.fn;
  });

  it('returns date only when boolean true is passed in', function () {
    testDate = new Date(2015, 4, 3, 7, 34, 56);
    expect(helper(testDate, true)).toEqual('05/03/2015');
  });

  it('returns datetime when stringy truthy value is passed in', function () {
    var timezone = moment(
      '2015-05-03T12:34:45Z').tz(moment.tz.guess()).format('Z');
    testDate = new Date(2015, 4, 3, 7, 34, 56);

    expect(
      helper(testDate, 'true')).toEqual('05/03/2015 07:34:56 AM ' + timezone);
  });

  it('returns datetime when stringy falsey value is passed in', function () {
    var timezone = moment(
      '2015-05-03T12:34:45Z').tz(moment.tz.guess()).format('Z');
    testDate = new Date(2015, 4, 3, 7, 34, 56);

    expect(
      helper(testDate, 'false')).toEqual('05/03/2015 07:34:56 AM ' + timezone);
  });

  it('returns datetime when false value is passed in', function () {
    var timezone = moment(
      '2015-05-03T12:34:45Z').tz(moment.tz.guess()).format('Z');
    testDate = new Date(2015, 4, 3, 7, 34, 56);

    expect(
      helper(testDate, false)).toEqual('05/03/2015 07:34:56 AM ' + timezone);
  });

  it('returns datetime when random values are passed in', function () {
    var timezone = moment(
      '2015-05-03T12:34:45Z').tz(moment.tz.guess()).format('Z');
    testDate = new Date(2015, 4, 3, 7, 34, 56);

    expect(
      helper(testDate, 'asdasd')).toEqual('05/03/2015 07:34:56 AM ' + timezone);
    expect(
      helper(testDate, {a: 1})).toEqual('05/03/2015 07:34:56 AM ' + timezone);
    expect(
      helper(testDate, '{a: 1}')).toEqual('05/03/2015 07:34:56 AM ' + timezone);
    expect(
      helper(testDate, 123)).toEqual('05/03/2015 07:34:56 AM ' + timezone);
  });
});
