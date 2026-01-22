const path = require("path");
const HtmlWebpackPlugin = require("html-webpack-plugin");
const fs = require("fs");
const webpack = require("webpack");

const { InjectManifest } = require("workbox-webpack-plugin");

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

  const apiUrl =
    env.API_URL || process.env.API_URL || "https://admin.portfolio.local";

  const enableShootingStars =
    env.ENABLE_SHOOTING_STARS || process.env.ENABLE_SHOOTING_STARS || "true";

  return {
    entry: "./src/index.tsx",
    output: {
      path: path.resolve(__dirname, "dist"),
      filename: "[name].[contenthash].js",
      chunkFilename: "[name].[contenthash].js",
      publicPath: "/",
      clean: true,
    },
    optimization: {
      splitChunks: {
        chunks: "all",
        cacheGroups: {
          vendor: {
            test: /[\\/]node_modules[\\/]/,
            name: "vendors",
            chunks: "all",
          },
        },
      },
    },
    devtool:
      argv.mode === "development"
        ? "eval-cheap-module-source-map"
        : "source-map",
    module: {
      rules: [
        {
          test: /\.(js|jsx|ts|tsx)$/,
          exclude: /node_modules/,
          use: {
            loader: "babel-loader",
            options: {
              cacheDirectory: true,
            },
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
      new webpack.DefinePlugin({
        "process.env.API_URL": JSON.stringify(apiUrl),
        "process.env.ENABLE_SHOOTING_STARS":
          JSON.stringify(enableShootingStars),
      }),
      // Only include the service worker plugin in production to avoid HMR issues
      ...(argv.mode !== "development"
        ? [
            new InjectManifest({
              swSrc: "./src/service-worker.ts",
              swDest: "service-worker.js",
              exclude: [/\.map$/, /asset-manifest\.json$/, /LICENSE/],
            }),
          ]
        : []),
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
      server: "http",
      allowedHosts: "all",
      client: {
        webSocketURL: "wss://portfolio.local/ws",
      },
    },
    resolve: {
      extensions: [".js", ".jsx", ".ts", ".tsx"],
    },
  };
};
