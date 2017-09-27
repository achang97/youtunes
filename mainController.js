'use strict';

var youtunesApp = angular.module('youtunesApp', ['ngRoute', 'ngMaterial', 'ngResource', 'ngAnimate', 'ngCookies', 'angular-loading-bar', 'youtube-embed']);

youtunesApp.config(function ($routeProvider) {

        $routeProvider.
            when('/home', {
                templateUrl: 'components/home-view/home-viewTemplate.html',
                controller: 'HomeViewController',
                reloadOnSearch: false
            }).
            when('/browse', {
                templateUrl: 'components/browse-view/browse-viewTemplate.html',
                controller: 'BrowseViewController'
            }).
            when('/youtubeSearch/:query/:stage', {
                templateUrl: 'components/youtube-search-view/youtube-search-viewTemplate.html',
                controller: 'YoutubeSearchViewController'
            }).
            when('/selectInformation/:query/:id', {
                templateUrl: 'components/select-information-view/select-information-viewTemplate.html',
                controller: 'SelectInformationViewController'
            }).       
            when('/download/:id', {
                templateUrl: 'components/download-view/download-viewTemplate.html',
                controller: 'DownloadViewController'
            }).
            otherwise({
                redirectTo: '/home'
            });    
        });


// results view
youtunesApp.directive('resultsDisplay', [function() {
    return {
        restrict: 'E',
        transclude: true,
        scope: {
            type: '@',
            results: '=',
            selectFn: '&',
            imgOnClickFn: '&'
        },
        // object is passed while making the call
        templateUrl: "directives/results-display/results-displayTemplate.html",
        // link: function (scope) {    
        // }
    }
}]);


youtunesApp.directive('spotifyPlayer', ['$sce', function($sce) {
    return {
        restrict: 'E',
        scope: {
            chosenUri: '='
        },
        // object is passed while making the call
        templateUrl: "directives/spotify-player/spotify-playerTemplate.html",
        link: function (scope) {
            scope.getTrustedUrl = function () {
                return $sce.trustAsResourceUrl('https://open.spotify.com/embed?uri=' + scope.chosenUri);
            };
        }
    }
}]);


youtunesApp.directive('searchBar', [function() {
    return {
        restrict: 'E',
        transclude: true,
        scope: {
            placeholder: '@',
            searchVar: '=',
            searchFn: '&'
        },
        // object is passed while making the call
        templateUrl: "directives/search-bar/search-barTemplate.html",
        link: function (scope) {

        }
    }
}]);







youtunesApp.controller('MainController', ['$scope', '$rootScope', '$location', '$mdDialog', '$resource', '$cookies',
    function ($scope, $rootScope, $location, $mdDialog, $resource, $cookies) {
        $scope.main = {};
        $scope.main.title = 'YouTunes';

        $rootScope.$on('$routeChangeStart', function() { 
            $mdDialog.cancel(); 
        });

        $scope.home = function () {
            $location.path('/home');
        };

        $scope.isLoggedIn = function () {
            return $scope.main.spotifyName !== undefined;
        };

        $scope.setUri = function (uri) {
            $scope.main.chosenUri = uri;
        };

        $scope.logout = function () {
            var logoutRes = $resource('/spotifyLogout');
            var logoutInfo = logoutRes.save({}, function () {
                $scope.main.spotifyName = undefined;
                $scope.main.spotifyImgUrl = undefined;
                console.log('Logged out!');
            }, function (err) {
                console.log('Failed to log out.');
            })
        };

        $scope.storeCookies = function (trackInfo) {
            var filteredTrackInfo = [
                {'display': 'Song', 'attribute': 'song_name', 'value': trackInfo.song_name},
                {'display': 'Artists', 'attribute': 'artists', 'value': trackInfo.artists ? trackInfo.artists : []},
                {'display': 'Album', 'attribute': 'album_name', 'value': trackInfo.album_name},
                {'display': 'Album Artists', 'attribute': 'album_artists', 'value': trackInfo.album_artists ? trackInfo.album_artists : []},
                {'display': 'Album Art Url', 'attribute': 'album_art_url', 'value': trackInfo.album_art_url}
            ];
            $cookies.putObject('spotifyInformation', filteredTrackInfo);
        };

        // try to fetch logged in info
        $scope.main.spotifyLoading = true;

        var spotifyRes = $resource('/getSpotifyInfo')
        var spotifyInfo = spotifyRes.get({}, function () {
            // store in scope
            $scope.main.spotifyName = spotifyInfo.name.split(" ")[0];
            $scope.main.spotifyImgUrl = spotifyInfo.img_url;
            $scope.main.spotifyLoading = false;
        }, function (err) {
            console.log('No Spotify information.');
            $scope.main.spotifyLoading = false;
        });    

    }]);
