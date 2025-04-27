// src/components/UserForm.js
import { useState } from 'react';
import api from '../api';

export default function UserForm({ onCreated }) {
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');

  const create = async () => {
    try {
      const res = await api.post('/users', { username, email });
      onCreated(res.data);
      setUsername('');
      setEmail('');
    } catch (err) {
      console.error(err);
      alert('생성 중 오류 발생');
    }
  };

  return (
    <div>
      <input
        type="text"
        placeholder="사용자 이름"
        value={username}
        onChange={e => setUsername(e.target.value)}
      />
      <input
        type="email"
        placeholder="이메일"
        value={email}
        onChange={e => setEmail(e.target.value)}
      />
      <button onClick={create}>사용자 등록</button>
    </div>
  );
}
