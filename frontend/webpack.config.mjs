import path from 'path';
import { fileURLToPath } from 'url';
import fs from 'fs';
import webpack from 'webpack';
import HtmlWebpackPlugin from 'html-webpack-plugin';
import { InjectManifest } from 'workbox-webpack-plugin';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

export default (env, argv) => {
  // Check for SSL certificates via environment variables
  const sslKeyPath = env.SSL_KEY_PATH || process.env.SSL_KEY_PATH;
  const sslCertPath = env.SSL_CRT_PATH || process.env.SSL_CRT_PATH;

  let httpsConfig = false;
  if (
    sslKeyPath &&
    sslCertPath &&
    fs.existsSync(sslKeyPath) &&
    fs.existsSync(sslCertPath)
  ) {
    try {
      httpsConfig = {
        key: fs.readFileSync(sslKeyPath),
        cert: fs.readFileSync(sslCertPath),
      };
    } catch (error) {
      console.warn('Error reading SSL certificates:', error.message);
      httpsConfig = false;
    }
  } else {
    // Only warn in dev mode to avoid cluttering prod build logs
    if (argv.mode === 'development') {
      console.warn('SSL certificates not found, running without HTTPS');
    }
  }

  const isDev = argv.mode === 'development';

  const apiUrl =
    env.API_URL ||
    process.env.API_URL ||
    (isDev ? 'https://api.portfolio.local' : '');

  if (!apiUrl && !isDev) {
    console.error(
      '\x1b[31m%s\x1b[0m',
      'BUILD ERROR: API_URL environment variable is required for production builds.'
    );
  }

  return {
    entry: './src/index.tsx',
    output: {
      path: path.resolve(__dirname, 'dist'),
      filename: '[name].[contenthash].js',
      chunkFilename: '[name].[contenthash].js',
      publicPath: '/',
      clean: true,
    },
    optimization: {
      splitChunks: {
        chunks: 'all',
        cacheGroups: {
          vendor: {
            test: /[\\/]node_modules[\\/]/,
            name: 'vendors',
            chunks: 'all',
          },
        },
      },
    },
    devtool:
      argv.mode === 'development'
        ? 'eval-cheap-module-source-map'
        : 'source-map',
    module: {
      rules: [
        {
          test: /\.(js|jsx|ts|tsx)$/,
          exclude: /node_modules/,
          use: {
            loader: 'babel-loader',
            options: {
              cacheDirectory: true,
            },
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
      new webpack.DefinePlugin({
        'process.env.API_URL': JSON.stringify(apiUrl),
      }),
      // Only include the service worker plugin in production to avoid HMR issues
      ...(argv.mode !== 'development'
        ? [
            new InjectManifest({
              swSrc: './src/service-worker.ts',
              swDest: 'service-worker.js',
              exclude: [/\.map$/, /asset-manifest\.json$/, /LICENSE/],
            }),
          ]
        : []),
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
      server: {
        type: httpsConfig ? 'https' : 'http',
        options: httpsConfig || undefined,
      },
      allowedHosts: 'all',
      client: {
        webSocketURL: 'wss://portfolio.local/ws',
      },
    },
    resolve: {
      extensions: ['.js', '.jsx', '.ts', '.tsx'],
    },
  };
};
