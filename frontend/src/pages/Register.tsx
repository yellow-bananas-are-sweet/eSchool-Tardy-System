import { IonCard, IonCardContent, IonCardHeader, IonCardTitle } from '@ionic/react';

const Register: React.FC = () => {
  return (
    <div className="ion-align-items-center centered-div">
      <IonCard className="ion-text-center ion-padding rounded-card" style={{ width: 'fit-content', height: 'fit-content', borderRadius: '10px' }}>
        <IonCardHeader>
          <IonCardTitle>Register Page</IonCardTitle>
        </IonCardHeader>
        <IonCardContent>
          Register Page Work in Proress
        </IonCardContent>
      </IonCard>
    </div>
  );
};

export default Register;