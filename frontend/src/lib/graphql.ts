import { GraphQLClient } from 'graphql-request';

const endpoint = 'http://127.0.0.1:8081/graphql';

export const client = new GraphQLClient(endpoint, {
  headers: {
    // If you have auth, add here, e.g. Authorization: `Bearer ${TOKEN}`
  },
});