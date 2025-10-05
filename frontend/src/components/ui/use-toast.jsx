import * as ToastPrimitives from "@radix-ui/react-toast";

export const toast = ({ variant, title, description, ...props }) => {
  ToastPrimitives.useToast().toast({
    title,
    description,
    variant: variant || "default",
    ...props,
  });
};