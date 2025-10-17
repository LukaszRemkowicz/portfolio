const path = require("path");
const HtmlWebpackPlugin = require("html-webpack-plugin");
const fs = require("fs");

module.exports = (env, argv) => {
  // Check if SSL certificates exist for devServer (both dev and prod can use HTTPS)
  let httpsConfig = false;
  try {
    httpsConfig = {
      key: fs.readFileSync("/etc/ssl/certs/portfolio.local.key"),
      cert: fs.readFileSync("/etc/ssl/certs/portfolio.local.crt"),
    };
  } catch (error) {
    console.warn("SSL certificates not found, running without HTTPS");
    httpsConfig = false;
  }

  return {
    entry: "./src/index.tsx",
    output: {
      path: path.resolve(__dirname, "dist"),
      filename: "bundle.js",
      publicPath: "/",
    },
    module: {
      rules: [
        {
          test: /\.(js|jsx|ts|tsx)$/,
          exclude: /node_modules/,
          use: {
            loader: "babel-loader",
          },
        },
        {
          test: /\.css$/,
          use: ["style-loader", "css-loader"],
        },
        {
          test: /\.(png|jpe?g|gif)$/i,
          use: [
            {
              loader: "file-loader",
            },
          ],
        },
      ],
    },
    plugins: [
      new HtmlWebpackPlugin({
        template: "./public/index.html",
      }),
    ],
    devServer: {
      static: {
        directory: path.join(__dirname, "public"),
      },
      host: "0.0.0.0",
      port: 3000,
      open: true,
      hot: true,
      historyApiFallback: true,
      server: httpsConfig ? "https" : "http",
      allowedHosts: "all",
      client: {
        webSocketURL: httpsConfig
          ? "wss://portfolio.local/ws"
          : "ws://portfolio.local/ws",
      },
    },
    resolve: {
      extensions: [".js", ".jsx", ".ts", ".tsx"],
    },
  };
};
