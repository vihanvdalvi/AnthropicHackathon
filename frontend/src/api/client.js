import axios from 'axios'

const api = axios.create({ baseURL: '/api' })

export const createUser = () =>
  api.post('/users').then(r => r.data)

export const submitPost = (user_id, text) =>
  api.post('/posts', { user_id, text }).then(r => r.data)

export const getIssues = () =>
  api.get('/issues').then(r => r.data)

export const getIssue = (id) =>
  api.get(`/issues/${id}`).then(r => r.data)

export const submitSurvey = (payload) =>
  api.post('/survey', payload).then(r => r.data)

export const getStats = (issue_id) =>
  api.get(`/stats/${issue_id}`).then(r => r.data)
