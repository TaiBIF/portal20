const path = require('path');

module.exports = (env) => {
  const env_name = (env.dev === true) ? '.dev.js' : '.min.js';
  return {
    entry: {
      'search': './src/search.js',
      'dataset-table': './src/dataset-table.js'
    },
    output: {
      path: path.join(__dirname, 'static/js'),
      filename: `[name]${env_name}`,
    },
    module: {
      rules: [
        {
          test: /\.js$/,
          exclude: /node_modules/,
          loader: 'babel-loader'
        },
        {
          test: /\.css$/,
          use: ['style-loader', 'css-loader']
        }
      ],
    },
    /*devtool: 'cheap-module-eval-source-map'*/
  }
};
