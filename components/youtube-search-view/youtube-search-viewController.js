'use strict';

youtunesApp.controller('YoutubeSearchViewController', ['$scope', '$resource', '$mdDialog', '$location', '$routeParams',
  function($scope, $resource, $mdDialog, $location, $routeParams) {
    $scope.main.title = 'YouTube Search';

    $scope.search = function () {
    	if (!$scope.main.resultsQuery) {
    		return;
    	}

    	// change path
    	$location.path('/youtubeSearch/' + $scope.main.resultsQuery + '/' + stage);

    	$scope.loading = true;
    	var youtubeRes = $resource('/searchYoutube');
    	var youtubeInfo = youtubeRes.get({query: $scope.main.resultsQuery}, function () {
    		// display the results
    		$scope.allVideos = youtubeInfo.results;
    		$scope.allVideos.forEach(function(currValue) {
    			currValue.date = new Date(currValue.date);
    		});
    		$scope.loading = false;
    	}, function (err) {
    		$scope.loading = false;
    		console.log(err);
    	});
    };

    $scope.main.resultsQuery = $routeParams.query;
    var stage = $routeParams.stage;
    $scope.search(); 

	$scope.selectVideo = function (video) {
		console.log(video)
		if (stage === '1') {
			// pass this to new view?
			$location.path('/selectInformation/' + $routeParams.query + '/' + video.id);
		} else {
			// // go directly to download page
			// if (!$scope.isLoggedIn()) {
			// 	$scope.storeCookies({});
			// }
			$location.path('/download/' + video.id);
		}
	};

	$scope.showAdvanced = function(ev, index) {
		$mdDialog.show({
			controller: DialogController,
			templateUrl: 'components/dialog-view/dialog-viewTemplate.html',
			parent: angular.element(document.body),
			targetEvent: ev,
			clickOutsideToClose:true,
			resolve: {
				videos: function() {
					return $scope.allVideos;
				},
				index: function () {
					return index;
				},
				query: function () {
					return $routeParams.query;
				},
				stage: function () {
					return stage;
				}
			}
		});
	};

	function DialogController($scope, $mdDialog, videos, index, query, stage) {
		$scope.allVideos = videos;
		$scope.index = index;
		var searchQuery = query;
		var stageParam = stage;

		var length = $scope.allVideos.length;

		$scope.goLeft = function () {
			$scope.index = ($scope.index + length - 1) % length;
		};

		$scope.goRight = function () {
			$scope.index = ($scope.index + 1) % length;
		};

		$scope.exit = function () {
			$mdDialog.hide();
		};

		$scope.selectVideo = function () {
			if (stage === '1') {
				// go to select information
				$location.path('/selectInformation/' + searchQuery + '/' + $scope.allVideos[$scope.index].id);
			} else if (stage === '2') {
				// go directly to download page
				$location.path('/download/' + $scope.allVideos[$scope.index].id);
			}
		};

		$scope.key = function($event){
			if ($event.keyCode == 27) {
				$scope.exit();
			} else if ($event.keyCode == 39) {
				$scope.goRight();
			} else if ($event.keyCode == 37) {
				$scope.goLeft();
			}
		}
	}

}]);