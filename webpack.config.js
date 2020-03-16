const path = require('path');

module.exports = (env) => {
  const output_name = (env === 'dev') ? 'bundle.js' : 'bundle.min.js';
  return {
    entry: './src/app.js',
    output: {
      path: path.join(__dirname, 'static/js'),
      filename: output_name
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
    devtool: 'cheap-module-eval-source-map'
  }
};
