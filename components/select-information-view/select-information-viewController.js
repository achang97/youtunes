youtunesApp.controller('SelectInformationViewController', ['$scope', '$resource', '$routeParams', '$location',
  function($scope, $resource, $routeParams, $location) {

    // // if not logged in, should not be on this page
    // // redirect to home
    // if (!$scope.isLoggedIn()) {
    //   $location.path('/home');
    //   return;
    // }

  	$scope.main.title = 'Select Information';

  	$scope.search = function () {

      if (!$scope.main.spotifyQuery) {
        return;
      }

  		var searchRes = $resource('searchSpotify');

      // change location
      $location.path('/selectInformation/' + $scope.main.spotifyQuery + '/' + $routeParams.id);

  		var searchInfo = searchRes.get({query: $scope.main.spotifyQuery}, function () {
  			$scope.allSpotifyResults = searchInfo.tracks;
  		}, function (err) {
  			console.log(err);
  		});
  	};

    // default
    $scope.main.spotifyQuery = $routeParams.query;
    $scope.search();


  	$scope.selectResult = function (result) {
      $scope.storeCookies(result);      
  		$location.path('/download/' + $routeParams.id);
  	};
}]);