import { GraphQLClient } from 'graphql-request';

const endpoint = import.meta.env.VITE_WORDPRESS_API_URL || 'http://localhost:8888/wp/graphql';


export const client = new GraphQLClient(endpoint, {
  headers: {
    'Content-Type': 'application/json',
  },
});
