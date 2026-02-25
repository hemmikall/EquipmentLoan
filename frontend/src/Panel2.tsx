// Import for type checking
import {
  ApiEndpoints,
  apiUrl,
  checkPluginVersion,
  type InvenTreePluginContext,
  ModelType
} from '@inventreedb/ui';
import {
  Alert,
  Button,
  Group,
  SimpleGrid,
  Stack,
  Text,
  Title
} from '@mantine/core';
import { notifications } from '@mantine/notifications';
import { useCallback, useEffect, useMemo, useState } from 'react';

interface PluginSettings {
  CUSTOM_VALUE: any;
  EQUIPMENTLOAN_LOAN_EQUIPMENT: boolean;
}

export function useMyPluginSettings() {
  const [settings, setSettings] = useState<PluginSettings | null>(null);

  useEffect(() => {
    fetch('/plugin/equipmentloan/settings/', {
      credentials: 'include'
    })
      .then((res) => res.json())
      .then((data) => setSettings(data));
  }, []);

  return settings;
}

/**
 * Render a custom panel with the provided context.
 * Refer to the InvenTree documentation for the context interface
 * https://docs.inventree.org/en/latest/plugins/mixins/ui/#plugin-context
 */
function EquipmentLoanPanel2({ context }: { context: InvenTreePluginContext }) {
  // React hooks can be used within plugin components
  useEffect(() => {
    console.log('useEffect in plugin component:');
    console.log('- Model:', context.model);
    console.log('- ID:', context.id);
  }, [context.model, context.id]);

  // Memoize the part ID as passed via the context object
  const partId = useMemo(() => {
    return context.model == ModelType.part ? context.id || null : null;
  }, [context.model, context.id]);

  // Hello world - counter example
  const [counter, setCounter] = useState<number>(0);

  // Extract context information
  const instance: string = useMemo(() => {
    const data = context?.instance ?? {};
    return JSON.stringify(data, null, 2);
  }, [context.instance]);

  // Custom form to edit the selected part
  const editPartForm = context.forms.edit({
    url: apiUrl(ApiEndpoints.part_list, partId),
    title: 'Edit Part',
    preFormContent: (
      <Alert title='Custom Plugin Form' color='blue'>
        This is a custom form launched from within a plugin!
      </Alert>
    ),
    fields: {
      name: {},
      description: {},
      category: {},
      pluginmetadata: {}
    },
    successMessage: null,
    onFormSuccess: () => {
      notifications.show({
        title: 'Success',
        message: 'Part updated successfully!',
        color: 'green'
      });
    }
  });

  // Custom callback function example
  const openForm = useCallback(() => {
    editPartForm?.open();
  }, [editPartForm]);

  // Navigation functionality example
  const gotoDashboard = useCallback(() => {
    context.navigate('/home');
  }, [context]);

  return (
    <>
      {editPartForm.modal}
      <Stack gap='xs'>
        <Title c={context.theme.primaryColor} order={3}>
          EquipmentLoan
        </Title>
        <text>
          Setting Value: {useMyPluginSettings()?.EQUIPMENTLOAN_LOAN_EQUIPMENT}
        </text>
        <Text>This is a custom panel for the EquipmentLoan plugin.</Text>
        <SimpleGrid cols={2}>
          <Group justify='apart' wrap='nowrap' gap='sm'>
            <Button color='blue' onClick={gotoDashboard}>
              Go to Dashboard
            </Button>
            {partId && (
              <Button color='green' onClick={openForm}>
                Edit Part
              </Button>
            )}
            <Button onClick={() => setCounter(counter + 1)}>
              Increment Counter
            </Button>
            <Text size='xl'>Counter: {counter}</Text>
          </Group>
          {instance ? (
            <Alert title='Instance Data' color='blue'>
              {instance}
            </Alert>
          ) : (
            <Alert title='No Instance' color='yellow'>
              No instance data available
            </Alert>
          )}
        </SimpleGrid>
      </Stack>
    </>
  );
}

// This is the function which is called by InvenTree to render the actual panel component
export function renderEquipmentLoanPanel2(context: InvenTreePluginContext) {
  checkPluginVersion(context);

  return <EquipmentLoanPanel2 context={context} />;
}
