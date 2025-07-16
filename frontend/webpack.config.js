const path = require('path');
const HtmlWebpackPlugin = require('html-webpack-plugin');
const fs = require('fs');

module.exports = {
  mode: 'development',
  entry: './src/index.jsx',
  output: {
    path: path.resolve(__dirname, 'dist'),
    filename: 'bundle.js',
    publicPath: '/',
  },
  module: {
    rules: [
      {
        test: /\.(js|jsx)$/,
        exclude: /node_modules/,
        use: {
          loader: 'babel-loader',
        },
      },
      {
        test: /\.css$/,
        use: ['style-loader', 'css-loader'],
      },
      {
        test: /\.(png|jpe?g|gif)$/i,
        use: [
          {
            loader: 'file-loader',
          },
        ],
      },
    ],
  },
  plugins: [
    new HtmlWebpackPlugin({
      template: './public/index.html',
    }),
  ],
  devServer: {
    static: {
      directory: path.join(__dirname, 'public'),
    },
    host: '0.0.0.0',
    port: 3000,
    open: true,
    hot: true,
    historyApiFallback: true,
    https: {
      key: fs.readFileSync('/etc/ssl/certs/portfolio.local.key'),
      cert: fs.readFileSync('/etc/ssl/certs/portfolio.local.crt'),
    },
    allowedHosts: 'all',
    client: {
      webSocketURL: 'wss://portfolio.local/ws',
    },
  },
  resolve: {
    extensions: ['.js', '.jsx'],
  },
}; 