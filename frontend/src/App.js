// src/App.js
import { useState, useEffect } from 'react';
import api from './api';
import IngredientForm from './components/IngredientForm';
import UserForm from './components/UserForm';

function App() {
  const [users, setUsers] = useState([]);
  const [ingredients, setIngredients] = useState([]);

  // 초기 데이터 로드
  useEffect(() => {
    api.get('/users').then(res => setUsers(res.data));
    api.get('/user_ingredients').then(res => setIngredients(res.data));
  }, []);

  return (
    <div style={{ padding: 20 }}>
      <h1>My Recipe App</h1>

      <section>
        <h2>사용자 등록</h2>
        <UserForm onCreated={u => setUsers([...users, u])} />
        <ul>
          {users.map(u => <li key={u.id}>{u.username} ({u.email})</li>)}
        </ul>
      </section>

      <section>
        <h2>재료 입력</h2>
        <IngredientForm onAdded={i => setIngredients([...ingredients, i])} />
        <ul>
          {ingredients.map(i => <li key={`${i.user_id}-${i.name}`}>{i.name}</li>)}
        </ul>
      </section>
    </div>
  );
}

export default App;
