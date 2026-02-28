import { type GrantedPower } from './GrantedPower';
import { type GrantedPowerName } from './GrantedPowerName';
export declare class GrantedPowerFactory {
    static grantedPowerClasses: Record<GrantedPowerName, new () => GrantedPower>;
    static make(name: GrantedPowerName): GrantedPower;
}
