'use strict';

youtunesApp.controller('HomeViewController', ['$scope', '$location', '$resource', '$window', '$routeParams',
  function($scope, $location, $resource, $window, $routeParams) {
    $scope.main.title = 'Home';

    function setError(message) {
        $scope.spotifySuccessful = false;
        $scope.error = message;
    }

    // store and get rid of error in url
    var error = $routeParams.error;
    if (error) {
        setError(error);
        $location.url($location.path())
    }

    $scope.spotifyLogin = function () {
        if ($scope.main.spotifyName) {
            // already logged in
            $scope.goToSearch();
            return;
        }

        var loginRes = $resource('/spotifyLogin');
        var loginInfo = loginRes.save({}, function () {
            var url = loginInfo.login_url;
            $window.location.href = url;
        }, function (err) {
            setError('Failed to load Spotify login page. Please try again.');
        });
    };

    $scope.goToSearch = function () {
    	$location.path('/browse');
    };
}]);