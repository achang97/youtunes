'use strict';

youtunesApp.controller('BrowseViewController', ['$scope', '$location', '$resource', '$cookies',
  function($scope, $location, $resource, $cookies) {
    $scope.main.title = 'Browse';

    var endpoints = ['/getSpotifyRecentlyPlayed', '/getSpotifyTopTracks', '/getSpotifySaved', '/getSpotifyNew'];
    
    $scope.spotifyTracks = [];

    var successCallback = function (info) {
        $scope.spotifyTracks.push({'type': info.type, 'tracks': info.tracks});
        console.log(info.type, info.tracks);
    };

    var failureCallback = function (err) {
        console.log(err);
    };

    endpoints.forEach(function (currEndpoint) {
        var res = $resource(currEndpoint);
        res.get({}, successCallback, failureCallback);
    });

    $scope.search = function () {
        if (!$scope.main.searchQuery) {
            return;
        }

        // 1 signals that search Youtube was used
        $location.path('/youtubeSearch/' + $scope.main.searchQuery + '/1');
    };


    $scope.directConvert = function () {
        if (!$scope.main.directConvertLink) {
            return;
        }

        // check
        var videoInfo = /(?:https?:\/{2})?(?:w{3}\.)?youtu(?:be)?\.(?:com|be)(?:\/watch\?v=|\/)([^\s&]+)/.exec($scope.main.directConvertLink);

        if (videoInfo) {
            // go to search
            $location.path('/selectInformation/' + videoInfo[1]);
        } else {
            $scope.showAlert('Please enter valid YouTube url.');
        }
    };


    $scope.searchWithSpotify = function (trackInfo) {
        // store information in cookies
        $scope.storeCookies(trackInfo);

        // go to search Youtube page, 2 signifies that Spotify was used
        var searchQuery = trackInfo.song_name + ' ' + trackInfo.artists.join(' ');
        $location.path('/youtubeSearch/' + searchQuery + '/2');
    }
}]);