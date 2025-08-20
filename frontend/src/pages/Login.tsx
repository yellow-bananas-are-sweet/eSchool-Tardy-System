import { IonCard, IonCardContent, IonCardHeader, IonCardTitle } from '@ionic/react';

const Login: React.FC = () => {
  return (
    <div className="ion-align-items-center centered-div">
      <IonCard className="ion-text-center ion-padding rounded-card" style={{ width: 'fit-content', height: 'fit-content', borderRadius: '10px' }}>
        <IonCardHeader>
          <IonCardTitle>Login Page</IonCardTitle>
        </IonCardHeader>
        <IonCardContent>
          Login Page Blank Template
        </IonCardContent>
      </IonCard>
    </div>
  );
};

export default Login;
