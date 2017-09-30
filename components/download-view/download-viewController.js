youtunesApp.controller('DownloadViewController', ['$scope', '$resource', '$routeParams', '$cookies', '$mdDialog', '$location',
  function($scope, $resource, $routeParams, $cookies, $mdDialog, $location) {

  	$scope.main.title = 'Download';

    if (!$cookies.getObject('spotifyInformation')) {
        $location.path('/home');
        return;
    }

    $scope.videoId = $routeParams.id;
    $scope.videoInfo = $cookies.getObject('spotifyInformation');


    $scope.play = function () {
        $scope.downloadPlayer.playVideo();
        $scope.playing = !$scope.playing;
    };

    $scope.pause = function () {
        $scope.downloadPlayer.pauseVideo();
        $scope.playing = !$scope.playing;
    };

    $scope.$on('youtube.player.ready', function ($event, player) {
        // play it again
        $scope.playerLoaded = true;
        console.log('ready!');
    });

    $scope.$on('youtube.player.error', function ($event, player) {
        // play it again
        $scope.playerError = true;
    });

    $scope.$on('youtube.player.ended', function ($event, player) {
        // reset the playing
        $scope.playing = false;
    });

    $scope.getDisplay = function (value) {
        if (Array.isArray(value)) {
            return value.join(', ');
        } else {
            return value;
        }
    };

    $scope.isArray = function (value) {
        return Array.isArray(value);
    };

    $scope.append = function (value) {
        value.push(undefined);
    };

    $scope.delete = function (index, value) {
        value = value.splice(index, 1);
    };

    var preeditVideoInfo;
    $scope.edit = function () {
        // toggle editedit
        $scope.isEditing = !$scope.isEditing;

        if ($scope.isEditing) {
            // store last video data
            preeditVideoInfo = JSON.parse(JSON.stringify($scope.videoInfo));
        } else {
            // saving, make sure array values are cleared of undefined values
            for (var i = 0; i < $scope.videoInfo.length; i++) {
                if (Array.isArray($scope.videoInfo[i].value)) {
                    $scope.videoInfo[i].value = $scope.videoInfo[i].value.filter(function (currEntry) {
                        return currEntry;
                    })
                }
            }

            // put it back in cookies
            $cookies.putObject('spotifyInformation', $scope.videoInfo);
        }
    };

    $scope.cancel = function () {
        $scope.isEditing = false;
        $scope.videoInfo = preeditVideoInfo;
    };

    var lastUsedVideoInfo;
    $scope.convert = function () {
        
        if ($scope.isEditing) {
            $scope.showAlert("Please save your changes before creating your mp3 file!");
            return;
        }

        // loop through and turn into map for backend use
        var backendInfo = {};
        var hasChanged = false;

        for (var i = 0; i < $scope.videoInfo.length; i++) {
            var currInfo = $scope.videoInfo[i];
            var attribute = currInfo['attribute'];
            backendInfo[attribute] = currInfo['value'];

            if (lastUsedVideoInfo && lastUsedVideoInfo[attribute] !== backendInfo[attribute]) {
                hasChanged = true;
            }
        }

        if (!hasChanged && lastUsedVideoInfo) {
            $scope.showAlert("You haven't made any changes since your last conversion.");
            return;
        }

        $scope.converting = true;

        var downloadRes = $resource('/download');
        var downloadInfo = downloadRes.save({id: $scope.videoId, info: backendInfo}, function () {
            $scope.backendDownloadName = downloadInfo.download;
            $scope.frontendDownloadName = backendInfo['song_name'];
            $scope.converting = false;

            // reset last used to prevent repetitive downloads
            lastUsedVideoInfo = backendInfo;
        }, function (err) {
            console.log(err);
            $scope.converting = false;

            $scope.showAlert('Failed to download the specified YouTube video. Please check to see all information is valid.')
        })        
    };


}]);