import { IonCard, IonCardContent, IonCardHeader, IonCardTitle } from '@ionic/react';
import './Home.css';

const Home: React.FC = () => {
  return (
    <div className="ion-align-items-center centered-div">
      <IonCard className="ion-text-center ion-padding rounded-card" style={{ width: 'fit-content', height: 'fit-content', borderRadius: '10px' }}>
        <IonCardHeader>
          <IonCardTitle>Welcome to the eSchool Tardy System</IonCardTitle>
        </IonCardHeader>
        <IonCardContent>
          To get started, please log in or register.
        </IonCardContent>
      </IonCard>
    </div>
  );
};

export default Home;
