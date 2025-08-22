import { IonButton, IonCard, IonCardContent, IonCardHeader, IonCardTitle, IonInput, IonInputPasswordToggle, IonItem, IonList } from '@ionic/react';
import React, { useState } from 'react';

const Login: React.FC = () => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');

  const loginUser = () => {
    console.log('Username: ', username);
    console.log('Password: ', password);
  }

  return (
    <div className="ion-align-items-center centered-div">
      <IonCard className="ion-text-center ion-padding rounded-card" style={{ width: 'fit-content', height: 'fit-content', borderRadius: '10px' }}>
        <IonCardHeader>
          <IonCardTitle>Login Page</IonCardTitle>
        </IonCardHeader>
        <IonCardContent>
          <IonList>
            <IonItem>
              <IonInput label="Username" labelPlacement='stacked'
                onIonChange={
                  (e) => {
                    setUsername(e.detail.value!);
                  }
                }
              />
            </IonItem>
            <IonItem>
              <IonInput type='password' label="Password" labelPlacement='stacked'
                onIonChange={
                  (e) => {
                    setPassword(e.detail.value!);
                  }
                }
              >
                <IonInputPasswordToggle slot="end" />
              </IonInput>
            </IonItem>
            <br />
            <IonButton shape="round" expand="block" onClick={loginUser}>Login</IonButton>
          </IonList>
        </IonCardContent>
      </IonCard>
    </div>
  );
};

export default Login;
