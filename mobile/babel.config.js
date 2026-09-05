module.exports = {
  presets: ['babel-preset-expo'],
  // Required by react-native-reanimated v4 (worklets moved to a separate package); without
  // this the app crashes at runtime the first time any animated component mounts. Must stay
  // last in the plugins list per reanimated's docs.
  plugins: ['react-native-worklets/plugin'],
};
