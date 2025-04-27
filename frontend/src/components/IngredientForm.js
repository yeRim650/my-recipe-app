// src/components/IngredientForm.js
import { useState } from 'react';
import api from '../api';

export default function IngredientForm({ onAdded }) {
  const [name, setName] = useState('');

  const add = async () => {
    if (!name.trim()) return;
    try {
      const res = await api.post('/user_ingredients', { name, user_id: 1 });
      onAdded(res.data);
      setName('');
    } catch (err) {
      console.error(err);
      alert('추가 중 오류 발생');
    }
  };

  return (
    <div>
      <input
        type="text"
        placeholder="재료 입력"
        value={name}
        onChange={e => setName(e.target.value)}
      />
      <button onClick={add}>추가</button>
    </div>
  );
}
