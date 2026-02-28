import type { GeneralPower } from './GeneralPower';
import type { GeneralPowerName } from './GeneralPowerName';
type Params = {
    name: GeneralPowerName;
};
export declare class GeneralPowerFactory {
    static generalPowerClasses: Record<GeneralPowerName, new () => GeneralPower>;
    static make(params: Params): GeneralPower;
}
export {};
